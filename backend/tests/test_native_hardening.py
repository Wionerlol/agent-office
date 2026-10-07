"""Hardening contracts; no Codex installation, model calls or credentials required."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

import backend.cli as wrapper
import backend.native_cli as cli
from backend.api.app import create_app
from backend.config import Settings
from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.native.codex.bindings import BindingConflict, BindingRegistry, NativeThreadBinding
from backend.native.codex.consumer import NativeBacklog
from backend.native.codex.diagnostics import validate_runtime
from backend.native.codex.profiles import PROFILES, profile_for
from backend.native.codex.protocol import (
    Fact,
    NativeConnectionFailure,
    NativeReadFailure,
    NativeUnavailable,
    ThreadMetadata,
    UnsupportedProtocol,
    project_event,
    require_version,
)
from backend.tests.test_codex_native import setup


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["--last"],
        ["resume"],
        ["resume", "--last"],
        ["resume", "session-name"],
        ["prompt", "resume"],
    ],
)
def test_ambiguous_launches_remain_unbound(args: list[str]) -> None:
    assert cli.explicit_thread(["codex", *args], None) is None


def test_explicit_launch_identity_and_conflicts() -> None:
    thread = str(uuid4())
    assert cli.explicit_thread(["codex", "resume", thread], None) == thread
    assert cli.explicit_thread(["codex"], thread) == thread
    assert cli.explicit_thread(["codex", "resume", thread], thread) == thread
    with pytest.raises(ValueError):
        cli.explicit_thread(["codex", "resume", thread], str(uuid4()))
    with pytest.raises(ValueError):
        cli.explicit_thread(["codex"], "not-a-uuid")


def test_devrouter_delimiter_and_environment_handshake(monkeypatch: pytest.MonkeyPatch) -> None:
    thread = str(uuid4())
    calls: dict[str, Any] = {}

    def run(command: list[str], **kwargs: Any) -> int:
        calls.update(command=command, **kwargs)
        return 0

    monkeypatch.setattr(wrapper, "run_wrapped", run)
    monkeypatch.setenv("AGENT_OFFICE_NATIVE_THREAD_ID", thread)
    with pytest.raises(SystemExit) as exit_info:
        wrapper.main(["--id", "devrouter-session", "codex", "--", "resume", thread])
    assert exit_info.value.code == 0
    assert calls["command"] == ["codex", "resume", thread]
    assert calls["native_handshake"].thread == thread
    assert calls["agent_id"] == "devrouter-session"


@pytest.mark.parametrize(
    "url",
    ["http://example.com", "https://127.0.0.1", "http://0.0.0.0", "http://name:password@localhost"],
)
def test_native_control_cli_stays_loopback(url: str) -> None:
    with pytest.raises(ValueError, match="loopback"):
        cli.local_server(url)


def test_background_handshake_retries_same_generation_without_raw_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requests: list[dict[str, Any]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"enabled": True})
        requests.append(json.loads(request.content))
        return httpx.Response(503 if len(requests) == 1 else 200, json={})

    original = httpx.Client
    monkeypatch.setattr(
        cli.httpx,
        "Client",
        lambda **kwargs: original(
            transport=httpx.MockTransport(respond),
            **kwargs,
        ),
    )
    agent = Agent(id="lead", name="Lead", provider="codex", repository=str(tmp_path))
    handshake = cli.BindingHandshake("http://127.0.0.1:8000/api/events", str(uuid4()))
    handshake._bind(agent)
    assert len(requests) == 2 and requests[0] == requests[1]
    assert requests[0]["expected_generation"] == agent.started_at.isoformat()
    assert requests[0]["office_agent_id"] == "lead"


@pytest.mark.asyncio
async def test_generation_guard_rejects_stale_handshake_before_native_read(tmp_path: Path) -> None:
    consumer = await setup(tmp_path)
    with pytest.raises(BindingConflict, match="Stale"):
        await consumer.bind("lead", "root", expected_generation="old-instance")


@pytest.mark.asyncio
async def test_concurrent_bindings_have_single_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import backend.native.codex.consumer as module

    c = await setup(tmp_path)
    c.bindings = BindingRegistry()
    c.adapter.bindings = c.bindings

    class Client:
        def __init__(self, *args: Any) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            await asyncio.sleep(0)
            return {
                "thread": {
                    "id": params["threadId"],
                    "cwd": str(tmp_path),
                    "status": {"type": "idle"},
                }
            }

    async def connection() -> tuple[str, Path]:
        return "0.160.1", tmp_path / "socket"

    async def idle(_: NativeThreadBinding) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(module, "ReadOnlyClient", Client)
    monkeypatch.setattr(c, "connection_info", connection)
    monkeypatch.setattr(c, "_run", idle)
    result = await asyncio.gather(
        c.bind("lead", "one"), c.bind("lead", "two"), return_exceptions=True
    )
    assert sum(isinstance(r, NativeThreadBinding) for r in result) == 1
    assert sum(isinstance(r, BindingConflict) for r in result) == 1
    assert len(c.bindings.by_thread) == 1
    await c.stop()


@pytest.mark.asyncio
async def test_registration_restart_during_bind_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import backend.native.codex.consumer as module

    c = await setup(tmp_path)
    c.bindings = BindingRegistry()
    c.adapter.bindings = c.bindings
    old = c.runtime.registry.get("lead")

    class Client:
        def __init__(self, *args: Any) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            await c.runtime.apply(AgentEvent(type=AgentEventType.AGENT_STOPPED, agent_id="lead"))
            new = old.model_copy(update={"started_at": datetime.now(UTC)})
            await c.runtime.apply(
                AgentEvent(
                    type=AgentEventType.AGENT_STARTED,
                    agent_id="lead",
                    payload={"agent": new.model_dump()},
                )
            )
            return {"thread": {"id": "one", "cwd": str(tmp_path), "status": {"type": "idle"}}}

    async def connection() -> tuple[str, Path]:
        return "0.160.1", tmp_path / "socket"

    monkeypatch.setattr(module, "ReadOnlyClient", Client)
    monkeypatch.setattr(c, "connection_info", connection)
    with pytest.raises(BindingConflict, match="changed"):
        await c.bind("lead", "one", expected_generation=old.started_at.isoformat())
    assert not c.bindings.by_thread


@pytest.mark.asyncio
async def test_child_failure_keeps_root_sibling_native_and_restores_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    c = await setup(tmp_path, definition=True)
    for child in ("bad", "sibling"):
        await c.adapter.create_child(
            "root", ThreadMetadata(child, tmp_path, "active", "root", "Nickname", None, False)
        )
        c.connected(child)
        await c.adapter.handle(
            Fact(
                "command",
                child,
                "turn",
                "test",
                phase="start",
                state=AgentState.TESTING,
                tool="test",
            )
        )
    c.connected("root")
    await c.adapter.handle(Fact("request", "root", "turn", "input", "request"))
    bad = c.bindings.by_thread["bad"].office_agent_id
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id=bad,
            payload={"command": "pytest"},
        )
    )
    await c.degrade("bad", NativeReadFailure("secret-question-output"), "child")
    assert c.runtime.registry.get(bad).status is AgentState.TESTING
    assert c.runtime.registry.get("lead").waiting_reason == "user_input"
    sibling = c.bindings.by_thread["sibling"].office_agent_id
    assert c.runtime.status_evidence(sibling).source is EventSource.NATIVE
    diagnostic = c.status()
    assert diagnostic["health"] == "degraded"
    assert "secret-question-output" not in json.dumps(diagnostic)
    row = next(b for b in diagnostic["bindings"] if b["office_agent_id"] == bad)
    assert row["fallback_active"] and row["failure_scope"] == "child"
    before = c.runtime.registry.get(bad).last_active_at
    await c.degrade("bad", NativeReadFailure("same"), "child")
    assert c.runtime.registry.get(bad).last_active_at == before

    class Client:
        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            return {
                "thread": {
                    "id": params["threadId"],
                    "cwd": str(tmp_path),
                    "status": {"type": "active"},
                    "parentThreadId": "root",
                }
            }

    async def hydrate(client: Any, thread: str) -> None:
        await c.adapter.handle(
            Fact(
                "command",
                thread,
                "new",
                "search",
                phase="start",
                state=AgentState.SEARCHING,
                tool="search",
            )
        )

    monkeypatch.setattr(c, "hydrate_thread", hydrate)
    await c.recover(Client(), "root")
    assert c.states["bad"] == "connected"
    assert c.runtime.registry.get(bad).status is AgentState.SEARCHING
    assert c.runtime.status_evidence(bad).source is EventSource.NATIVE


@pytest.mark.asyncio
async def test_root_failure_isolated_and_pending_wait_released(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    agent = Agent(id="other", name="Other", provider="codex", repository=str(tmp_path))
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            agent_id=agent.id,
            payload={"agent": agent.model_dump()},
        )
    )
    c.bindings.add(
        NativeThreadBinding("other", "other-root", "other-root", agent.started_at.isoformat())
    )
    await c.adapter.handle(
        Fact(
            "command",
            "other-root",
            "turn",
            "cmd",
            phase="start",
            state=AgentState.TESTING,
            tool="test",
        )
    )
    await c.adapter.handle(Fact("request", "root", "turn", "input", "request"))
    await c.degrade("root", NativeBacklog("backlog"), "root")
    assert c.runtime.registry.get("lead").waiting_reason is None
    assert c.runtime.registry.get("other").status is AgentState.TESTING
    assert c.runtime.status_evidence("other").source is EventSource.NATIVE
    with pytest.raises(NativeConnectionFailure):
        await c.degrade("root", NativeConnectionFailure("socket closed"), "child")


@pytest.mark.asyncio
async def test_child_read_error_is_retried_without_duplicate_agents(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    c.workspaces["root"] = tmp_path
    failing = True

    class Client:
        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if method == "thread/read":
                if failing:
                    raise NativeReadFailure("private output")
                return {
                    "thread": {
                        "id": "child",
                        "cwd": str(tmp_path),
                        "status": {"type": "active"},
                        "parentThreadId": "root",
                    }
                }
            return {"data": []}

    event = Fact("child", "root", "turn", "spawn", phase="started", child="child")
    await c.safe_consume(Client(), event)
    assert c.states["child"] == "degraded" and "child" in c.pending_children
    assert len(c.runtime.registry.all()) == 1
    failing = False
    await c.recover(Client(), "root")
    assert c.states["child"] == "connected" and not c.pending_children
    await c.safe_consume(Client(), event)
    assert len(c.runtime.registry.all()) == 2


@pytest.mark.parametrize("version", list(PROFILES))
def test_reviewed_profiles_are_explicit(version: str) -> None:
    assert require_version(version) is profile_for(version)
    assert "thread/read" in require_version(version).read_methods
    assert "turn/start" not in require_version(version).read_methods
    assert "fileChange" in require_version(version).item_types


def test_unknown_profile_and_selected_malformed_event_fail_closed(tmp_path: Path) -> None:
    assert profile_for("99.0.0") is None
    with pytest.raises(UnsupportedProtocol):
        require_version("99.0.0")
    with pytest.raises(NativeUnavailable):
        project_event(
            {
                "method": "item/started",
                "params": {"threadId": "root", "item": {"type": "fileChange"}},
            },
            tmp_path,
        )
    assert (
        project_event(
            {
                "method": "item/started",
                "params": {"threadId": "root", "item": {"type": "reasoning"}},
            },
            tmp_path,
        )
        is None
    )


@pytest.mark.asyncio
async def test_validation_unknown_version_never_connects(monkeypatch: pytest.MonkeyPatch) -> None:
    import backend.native.codex.diagnostics as module

    async def discover(binary: str) -> tuple[str, Path]:
        return "99.0.0", Path("unused")

    monkeypatch.setattr(module, "discover", discover)
    report = await validate_runtime(thread="root")
    assert report["protocol"] == "unsupported" and report["review_required"]
    assert report["checks"] == ["discovery"]


def test_disabled_and_unbound_diagnostics(tmp_path: Path) -> None:
    settings = Settings.for_project(tmp_path)
    with TestClient(create_app(settings)) as client:
        status = client.get("/api/native/codex").json()
        assert status["health"] == "disabled" and status["protocol"] == "unknown"
    settings.native.codex.enabled = True
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/native/codex").json()["health"] == "unbound"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failed_method", ["thread/read", "thread/resume", "thread/turns/list", "thread/items/list"]
)
async def test_validation_reports_safe_read_schema_failures(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failed_method: str,
) -> None:
    import backend.native.codex.diagnostics as module

    class Client:
        def __init__(self, *args: Any) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if method == failed_method:
                raise NativeReadFailure("sk-private-question-diff-output")
            if method in {"thread/read", "thread/resume"}:
                return {"thread": {"id": "root", "cwd": str(tmp_path), "status": {"type": "idle"}}}
            return {"data": [{"id": "turn", "status": "completed"}]}

    async def discovery(binary: str) -> tuple[str, Path]:
        return "0.160.1", tmp_path / "socket"

    monkeypatch.setattr(module, "ReadOnlyClient", Client)
    monkeypatch.setattr(module, "discover", discovery)
    result = await validate_runtime(thread="root")
    assert result["failed_check"] == failed_method and result["health"] == "unavailable"
    assert "sk-private" not in json.dumps(result)


@pytest.mark.asyncio
async def test_child_reconnect_preserves_root_transport(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.create_child(
        "root", ThreadMetadata("child", tmp_path, "active", "root", None, None, False)
    )
    child = c.bindings.by_thread["child"].office_agent_id
    transport = asyncio.create_task(asyncio.Event().wait())
    c.tasks["root"] = transport
    c.connected("root")
    await c.reconnect(child)
    assert c.tasks["root"] is transport and not transport.done()
    assert c.states["root"] == "connected" and c.states["child"] == "degraded"
    await c.stop()


@pytest.mark.asyncio
async def test_live_consumer_keeps_root_when_child_read_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import backend.native.codex.consumer as module

    c = await setup(tmp_path)
    c.workspaces["root"] = tmp_path
    c.settings.reconnect_seconds = 0.1
    await c.adapter.create_child(
        "root", ThreadMetadata("bad", tmp_path, "active", "root", None, None, False)
    )

    class Client:
        def __init__(self, *args: Any) -> None:
            self.reader = None

        async def __aenter__(self) -> "Client":
            self.reader = asyncio.create_task(asyncio.Event().wait())
            return self

        async def __aexit__(self, *args: Any) -> None:
            self.reader.cancel()
            await asyncio.gather(self.reader, return_exceptions=True)

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if params.get("threadId") == "bad":
                raise NativeReadFailure("private content")
            if method in {"thread/read", "thread/resume"}:
                return {
                    "thread": {"id": "root", "cwd": str(tmp_path), "status": {"type": "active"}}
                }
            return {"data": []}

    async def discovery(binary: str) -> tuple[str, Path]:
        return "0.160.1", tmp_path / "socket"

    monkeypatch.setattr(module, "ReadOnlyClient", Client)
    monkeypatch.setattr(module, "discover", discovery)
    degraded = asyncio.Event()
    original_degrade = c.degrade

    async def signal(thread: str, error: Exception, scope: str) -> None:
        await original_degrade(thread, error, scope)
        if thread == "bad":
            degraded.set()

    monkeypatch.setattr(c, "degrade", signal)
    c.tasks["root"] = asyncio.create_task(c._run(c.bindings.by_thread["root"]))
    async with asyncio.timeout(2):
        await degraded.wait()
    assert c.states["root"] == "connected"
    await asyncio.sleep(0.15)
    assert c.states["root"] == "connected" and not c.tasks["root"].done()
    await c.stop()
