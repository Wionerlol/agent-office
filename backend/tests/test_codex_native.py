"""Deterministic protocol/domain contracts, not claims of native provider capability."""

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import CodexNativeSettings, Settings
from backend.models import (
    Agent,
    AgentDefinition,
    AgentEvent,
    AgentEventType,
    AgentState,
    EventSource,
)
from backend.native.codex.activity import ReplayCache
from backend.native.codex.bindings import BindingConflict, BindingRegistry, NativeThreadBinding
from backend.native.codex.consumer import CodexNativeConsumer
from backend.native.codex.protocol import Fact, NativeUnavailable, ThreadMetadata, parse_event
from backend.native.codex.transport import ReadOnlyClient
from backend.runtime.office import OfficeRuntime
from backend.state.identity import AgentDefinitionRegistry


async def setup(tmp_path: Path, definition: bool = False) -> CodexNativeConsumer:
    settings = Settings.for_project(tmp_path)
    if definition:
        settings.agents = [
            AgentDefinition(
                id="tester",
                name="Tester",
                role="tester",
                responsibilities=["Run tests"],
            )
        ]
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings))
    agent = Agent(
        id="lead",
        name="Lead",
        provider="codex",
        repository=str(tmp_path),
        status=AgentState.THINKING,
    )
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            source=EventSource.WRAPPER,
            agent_id=agent.id,
            payload={"agent": agent.model_dump()},
        )
    )
    consumer = CodexNativeConsumer(runtime, CodexNativeSettings(enabled=True, terminal_seconds=0.1))
    consumer.bindings.add(
        NativeThreadBinding(
            "lead",
            "root",
            "root",
            agent.started_at.isoformat(),
            "tester" if definition else None,
        )
    )
    return consumer


def binding(agent: str = "lead", thread: str = "root") -> NativeThreadBinding:
    return NativeThreadBinding(agent, thread, thread, "generation")


def test_bindings_are_explicit_sticky_and_bounded() -> None:
    registry = BindingRegistry(capacity=1)
    registry.add(binding())
    registry.add(binding())
    for other in (binding("other"), binding(thread="other"), binding("next", "next")):
        with pytest.raises(BindingConflict):
            registry.add(other)
    assert registry.by_thread["root"].office_agent_id == "lead"


@pytest.mark.asyncio
async def test_domain_defaults_and_waiting_websocket_fields(tmp_path: Path) -> None:
    consumer = await setup(tmp_path)
    runtime = consumer.runtime
    assert runtime.registry.get("lead").waiting_reason is None
    queue = runtime.bus.subscribe()
    await consumer.adapter.handle(Fact("request", "root", "turn", "item", "request"))
    agent = runtime.registry.get("lead")
    assert agent.status is AgentState.WAITING
    assert agent.waiting_reason == "user_input"
    message = queue.get_nowait()
    assert message["type"] == "agent.updated"
    assert message["changes"]["waiting_reason"] == "user_input"
    before = agent.model_copy(deep=True)
    await consumer.adapter.handle(Fact("request", "root", "turn", "item", "request"))
    assert queue.empty()
    assert runtime.registry.get("lead") == before
    await consumer.adapter.handle(Fact("status", "root", phase="idle"))
    assert runtime.registry.get("lead").waiting_reason == "user_input"
    await consumer.adapter.handle(Fact("resolved", "root", request="request"))
    assert runtime.registry.get("lead").status is AgentState.IDLE
    assert runtime.registry.get("lead").waiting_reason is None
    assert queue.get_nowait()["changes"]["waiting_reason"] is None
    await consumer.adapter.handle(Fact("request", "root", "turn", "item", "request"))
    assert runtime.registry.get("lead").status is AgentState.IDLE


@pytest.mark.asyncio
async def test_idle_does_not_erase_waiting_flag_before_request_replay(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.handle(Fact("status", "root", phase="active", waiting=True))
    await c.adapter.handle(Fact("status", "root", phase="idle"))
    assert c.runtime.registry.get("lead").waiting_reason == "user_input"
    await c.adapter.handle(Fact("status", "root", phase="active", waiting=False))
    assert c.runtime.registry.get("lead").waiting_reason is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "command,state",
    [
        ("python -m pytest -q", AgentState.TESTING),
        ("rg term calc.py", AgentState.SEARCHING),
        ("printf hello", AgentState.TOOL_RUNNING),
    ],
)
async def test_native_command_classification_and_safe_completion(
    tmp_path: Path,
    command: str,
    state: AgentState,
) -> None:
    c = await setup(tmp_path)
    raw = {
        "method": "item/started",
        "params": {
            "threadId": "root",
            "turnId": "turn",
            "item": {
                "id": "tool",
                "type": "commandExecution",
                "command": command,
                "output": "sk-private-output",
            },
        },
    }
    fact = parse_event(raw, tmp_path)
    assert fact is not None
    assert "hello" not in repr(fact) and "sk-private" not in repr(fact)
    await c.adapter.handle(fact)
    assert c.runtime.registry.get("lead").status is state
    assert c.runtime.status_evidence("lead").source is EventSource.NATIVE
    await c.adapter.handle(replace(fact, phase="finish", exit_code=1))
    assert c.runtime.registry.get("lead").status is AgentState.THINKING
    assert c.runtime.registry.get("lead").metadata["native_exit_code"] == 1
    before = c.runtime.registry.get("lead").model_copy(deep=True)
    await c.adapter.handle(replace(fact, phase="finish", exit_code=1))
    await c.adapter.handle(fact)  # Out-of-order replayed start cannot revive a completed item.
    assert c.runtime.registry.get("lead") == before


@pytest.mark.asyncio
async def test_native_concurrency_waiting_tests_search_files_tools(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    a = c.adapter
    test = Fact(
        "command", "root", "turn", "test", phase="start", state=AgentState.TESTING, tool="test"
    )
    search = replace(test, item="search", state=AgentState.SEARCHING, tool="search")
    shell = replace(test, item="shell", state=AgentState.TOOL_RUNNING, tool="command")
    edit = Fact("file", "root", "turn", "edit", phase="start", paths=("calc.py",))
    for fact in (shell, edit, search, test):
        await a.handle(fact)
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    await a.handle(Fact("request", "root", "turn", "question", "request"))
    assert c.runtime.registry.get("lead").status is AgentState.WAITING
    await a.handle(replace(edit, phase="finish"))
    await a.handle(Fact("resolved", "root", request="request"))
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    assert c.runtime.registry.get("lead").changed_files == ["calc.py"]
    await a.handle(replace(test, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.SEARCHING
    edit2 = replace(edit, item="edit2")
    await a.handle(edit2)
    await a.handle(replace(search, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.CODING
    await a.handle(replace(edit2, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.TOOL_RUNNING
    await a.handle(replace(shell, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


def test_structural_parser_denies_content_paths_and_unknown_shapes(tmp_path: Path) -> None:
    base = {
        "method": "item/started",
        "params": {
            "threadId": "root",
            "turnId": "turn",
            "item": {
                "type": "fileChange",
                "id": "patch",
                "changes": [
                    {"path": str(tmp_path / "calc.py"), "diff": "sk-secret"},
                    {"path": "../../private.key", "diff": "private"},
                ],
            },
        },
    }
    fact = parse_event(base, tmp_path)
    assert fact and fact.paths == ("calc.py",)
    assert "secret" not in repr(fact) and "private" not in repr(fact)
    for raw in (
        {},
        {"method": "item/started", "params": None},
        {"method": "item/started", "params": {"threadId": "root", "item": []}},
    ):
        assert parse_event(raw, tmp_path) is None
    for kind in ("reasoning", "userMessage", "agentMessage", "mcpToolCall"):
        base["params"]["item"]["type"] = kind
        assert parse_event(base, tmp_path) is None


@pytest.mark.asyncio
async def test_child_identity_definition_parent_id_and_terminal_lifecycle(tmp_path: Path) -> None:
    c = await setup(tmp_path, definition=True)
    metadata = ThreadMetadata("child", tmp_path, "active", "root", "Averroes", None, False)
    await c.adapter.create_child("root", metadata)
    await c.adapter.create_child("root", metadata)
    assert len(c.runtime.registry.all()) == 2
    child = next(a for a in c.runtime.registry.all() if a.parent_agent_id)
    assert child.pid is None and child.parent_agent_id == "lead"
    assert child.name == "Tester" and child.role == "tester"
    assert child.responsibilities == ["Run tests"]
    assert child.metadata["native_nickname"] == "Averroes"
    assert c.bindings.by_thread["child"].office_agent_id == child.id
    await c.adapter.handle(Fact("request", "child", "turn", "item", "request"))
    await c.adapter.child_completed("child", successful=True)
    child = c.runtime.registry.get(child.id)
    assert child.status is AgentState.DONE and child.waiting_reason is None
    await asyncio.sleep(0.15)
    assert len(c.runtime.registry.all()) == 1
    await c.adapter.create_child("root", metadata)
    assert len(c.runtime.registry.all()) == 1
    assert "child" in c.bindings.by_thread  # Sticky tombstone survives UI cleanup.
    await c.stop()


@pytest.mark.asyncio
async def test_unregistered_child_nickname_is_fallback_and_error_is_preserved(
    tmp_path: Path,
) -> None:
    c = await setup(tmp_path)
    await c.adapter.create_child(
        "root",
        ThreadMetadata(
            "child",
            tmp_path,
            "active",
            "root",
            "Mendel",
            None,
            False,
        ),
    )
    child_id = c.bindings.by_thread["child"].office_agent_id
    assert c.runtime.registry.get(child_id).name == "Mendel"
    await c.adapter.handle(Fact("turn", "child", "turn", phase="failed"))
    await c.adapter.child_completed("child", successful=True)
    assert c.runtime.registry.get(child_id).status is AgentState.ERROR
    await c.stop()


@pytest.mark.asyncio
async def test_wait_on_child_is_only_deterministic_parent_child_mapping(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.create_child(
        "root",
        ThreadMetadata(
            "child",
            tmp_path,
            "active",
            "root",
            "Mendel",
            None,
            False,
        ),
    )
    assert c.runtime.registry.get("lead").status is AgentState.THINKING
    await c.adapter.handle(Fact("wait", "root", "turn", "unknown", phase="start"))
    assert c.runtime.registry.get("lead").waiting_reason is None
    await c.adapter.handle(
        Fact("wait", "root", "turn", "multiple", phase="start", recipients=("child", "unknown"))
    )
    assert c.runtime.registry.get("lead").waiting_reason is None
    known = Fact("wait", "root", "turn", "known", phase="start", recipients=("child",))
    await c.adapter.handle(known)
    assert c.runtime.registry.get("lead").waiting_reason == "child_agent"
    assert c.runtime.registry.get("lead").waiting_on_agent_id == (
        c.bindings.by_thread["child"].office_agent_id
    )
    await c.adapter.handle(replace(known, phase="finish"))
    assert c.runtime.registry.get("lead").waiting_reason is None
    await c.stop()


@pytest.mark.asyncio
async def test_disconnect_releases_native_evidence_and_fallbacks_remain(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.handle(Fact("request", "root", "turn", "item", "request"))
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"command": "pytest", "tool": "test"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.WAITING
    await c.adapter.release("root")
    assert c.runtime.registry.get("lead").waiting_reason is None
    assert c.runtime.status_evidence("lead").source is EventSource.TOOL_PROCESS
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"command": "pytest", "tool": "test"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    assert len(c.runtime.registry.all()) == 1
    assert c.bindings.by_agent["lead"].thread_id == "root"


def test_replay_cache_is_bounded_and_retains_recent_keys() -> None:
    cache = ReplayCache(capacity=2)
    for index in range(10):
        assert cache.add((index,))
    assert len(cache.entries) == 2
    assert not cache.add((9,))


class FakeClient:
    """Transport fixture for explicit binding and reconciliation contracts only."""

    metadata: dict[str, Any]
    requests: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, *_: object) -> None:
        pass

    async def __aenter__(self) -> "FakeClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        pass

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.requests.append((method, params))
        if method == "thread/read":
            return {"thread": self.metadata}
        if method == "thread/turns/list":
            return {"data": []}
        return {}


@pytest.mark.asyncio
async def test_binding_handshake_does_not_discover_threads_from_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import backend.native.codex.consumer as module

    c = await setup(tmp_path)
    c.bindings = BindingRegistry()
    c.adapter.bindings = c.bindings
    FakeClient.metadata = {"id": "selected", "cwd": str(tmp_path), "status": {"type": "idle"}}
    FakeClient.requests = []
    monkeypatch.setattr(module, "ReadOnlyClient", FakeClient)

    async def discovery(_: str) -> tuple[str, Path]:
        return "0.160.1", tmp_path / "socket"

    async def idle(_: NativeThreadBinding) -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(module, "discover", discovery)
    monkeypatch.setattr(c, "_run", idle)
    established = await c.bind("lead", "selected")
    assert established.office_agent_id == "lead" and established.thread_id == "selected"
    assert [m for m, _ in FakeClient.requests] == ["thread/read"]
    assert await c.bind("lead", "selected") == established
    with pytest.raises(BindingConflict):
        await c.bind("lead", "different")
    await c.reconnect("lead")
    assert c.bindings.by_agent["lead"] == established
    await c.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", ["disabled", "unavailable", "unsupported", "workspace"])
async def test_native_binding_failure_keeps_existing_office_usable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    problem: str,
) -> None:
    import backend.native.codex.consumer as module

    c = await setup(tmp_path)
    c.bindings = BindingRegistry()
    c.adapter.bindings = c.bindings
    c.settings.enabled = problem != "disabled"
    FakeClient.metadata = {"id": "selected", "cwd": "/other", "status": {"type": "idle"}}
    monkeypatch.setattr(module, "ReadOnlyClient", FakeClient)

    async def discovery(_: str) -> tuple[str, Path]:
        if problem == "unavailable":
            raise OSError("sk-secret-server-message")
        return "99.0.0" if problem == "unsupported" else "0.160.1", tmp_path / "socket"

    monkeypatch.setattr(module, "discover", discovery)
    with pytest.raises((NativeUnavailable, OSError, BindingConflict)):
        await c.bind("lead", "selected")
    assert not c.bindings.by_thread and len(c.runtime.registry.all()) == 1
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            agent_id="lead",
            source=EventSource.TOOL_PROCESS,
            payload={"command": "pytest"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    if problem == "unsupported":
        assert c.version == "99.0.0"


def test_api_requires_explicit_thread_id_and_is_safe_when_disabled(tmp_path: Path) -> None:
    with TestClient(create_app(Settings.for_project(tmp_path))) as client:
        assert client.get("/api/native/codex").json()["enabled"] is False
        assert (
            client.post(
                "/api/native/codex/bind",
                json={"office_agent_id": "lead", "repository": str(tmp_path)},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/native/codex/bind", json={"office_agent_id": "lead", "thread_id": "root"}
            ).status_code
            == 503
        )
        assert client.get("/health").status_code == 200


@pytest.mark.asyncio
async def test_readonly_transport_rejects_controls_before_sending(tmp_path: Path) -> None:
    async def ignore(_: dict[str, Any]) -> None:
        pass

    client = ReadOnlyClient(tmp_path / "socket", "0.160.1", ignore)
    for method in ("turn/start", "turn/interrupt", "thread/start", "approval/respond"):
        with pytest.raises(ValueError):
            await client.request(method, {})
    with pytest.raises(ValueError):
        await client.request(
            "thread/resume", {"threadId": "root", "excludeTurns": True, "model": "other"}
        )


@pytest.mark.asyncio
async def test_replayed_pending_requests_restore_without_duplicate_mutations(
    tmp_path: Path,
) -> None:
    c = await setup(tmp_path)
    first = Fact("request", "root", "turn", "q1", "r1")
    second = Fact("request", "root", "turn", "q2", "r2")
    await c.adapter.handle(first)
    await c.adapter.handle(second)
    await c.adapter.release("root")
    await c.adapter.handle(first)
    await c.adapter.handle(second)
    await c.adapter.handle(Fact("resolved", "root", request="r1"))
    assert c.runtime.registry.get("lead").waiting_reason == "user_input"
    await c.adapter.handle(Fact("resolved", "root", request="r2"))
    assert c.runtime.registry.get("lead").waiting_reason is None
    before = c.runtime.registry.get("lead").model_copy(deep=True)
    await c.adapter.handle(first)
    assert c.runtime.registry.get("lead") == before
    # A new turn/item disambiguates a request ID reused after a daemon reconnect.
    reused = Fact("request", "root", "new-turn", "q-new", "r1")
    await c.adapter.handle(reused)
    assert c.runtime.registry.get("lead").waiting_reason == "user_input"
    await c.adapter.handle(Fact("resolved", "root", request="r1"))
    assert c.runtime.registry.get("lead").waiting_reason is None


@pytest.mark.asyncio
async def test_repeated_outage_release_does_not_keep_resetting_idle_clock(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.handle(Fact("request", "root", "turn", "q", "r"))
    await c.adapter.release("root")
    before = c.runtime.registry.get("lead").model_copy(deep=True)
    for _ in range(3):
        await c.adapter.release("root")
    assert c.runtime.registry.get("lead") == before
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.STATE_CHANGED,
            source=EventSource.TIMEOUT,
            agent_id="lead",
            payload={"to": "idle"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.IDLE


@pytest.mark.asyncio
async def test_child_reactivation_cancels_terminal_cleanup_and_preserves_identity(
    tmp_path: Path,
) -> None:
    c = await setup(tmp_path)
    meta = ThreadMetadata("child", tmp_path, "active", "root", "Mendel", None, False)
    await c.adapter.create_child("root", meta)
    agent_id = c.bindings.by_thread["child"].office_agent_id
    await c.adapter.child_completed("child", successful=True)
    await c.adapter.handle(Fact("turn", "child", "next", phase="inProgress"))
    await asyncio.sleep(0.15)
    assert c.runtime.registry.get(agent_id).status is AgentState.THINKING
    await c.adapter.child_completed("child", successful=True)
    await asyncio.sleep(0.15)
    assert not c.adapter.live("child")
    # Consumer permits this only after an explicit fresh inProgress turn snapshot.
    await c.adapter.create_child("root", meta, reopen=True)
    assert c.bindings.by_thread["child"].office_agent_id == agent_id
    assert c.adapter.live("child")
    await c.stop()


@pytest.mark.asyncio
async def test_child_cannot_change_parent_and_completed_wait_is_safe(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    meta = ThreadMetadata("child", tmp_path, "active", "root", "Mendel", None, False)
    await c.adapter.create_child("root", meta)
    with pytest.raises(BindingConflict):
        await c.adapter.create_child("root", replace(meta, parent="different"))
    await c.adapter.child_completed("child", successful=True)
    await asyncio.sleep(0.15)
    await c.adapter.handle(
        Fact("wait", "root", "turn", "wait", phase="start", recipients=("child",))
    )
    assert c.runtime.registry.get("lead").waiting_reason is None
    await c.stop()


@pytest.mark.asyncio
async def test_failed_patch_does_not_claim_files_changed(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    edit = Fact("file", "root", "turn", "edit", phase="start", paths=("calc.py",))
    await c.adapter.handle(edit)
    await c.adapter.handle(replace(edit, phase="finish", successful=False))
    assert c.runtime.registry.get("lead").changed_files == []
    assert c.runtime.registry.get("lead").status is AgentState.THINKING
    await c.adapter.handle(edit)
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


@pytest.mark.asyncio
async def test_terminal_error_evidence_cannot_be_released_into_fallback(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.adapter.handle(Fact("turn", "root", "turn", phase="failed"))
    await c.adapter.release("root")
    assert not c.runtime.status_evidence("lead").released
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"command": "pytest"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.ERROR


@pytest.mark.asyncio
async def test_snapshot_hydration_restores_active_command_and_waits_safely(tmp_path: Path) -> None:
    c = await setup(tmp_path)

    class SnapshotClient:
        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if method == "thread/read":
                return {
                    "thread": {
                        "id": "root",
                        "cwd": str(tmp_path),
                        "status": {"type": "active", "activeFlags": []},
                    }
                }
            if method == "thread/turns/list":
                return {"data": [{"id": "turn", "status": "inProgress"}]}
            return {
                "data": [
                    {
                        "item": {
                            "id": "test",
                            "type": "commandExecution",
                            "command": "pytest",
                            "status": "inProgress",
                        }
                    }
                ]
            }

    await c.adapter.handle(
        Fact(
            "command", "root", "turn", "test", phase="start", state=AgentState.TESTING, tool="test"
        )
    )
    await c.adapter.release("root")
    await c.hydrate_thread(SnapshotClient(), "root")
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    await c.adapter.handle(Fact("command", "root", "turn", "test", phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


@pytest.mark.asyncio
async def test_child_spawn_consumer_deduplicates_before_second_subscription(tmp_path: Path) -> None:
    c = await setup(tmp_path, definition=True)

    class ChildClient:
        subscriptions = 0

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if method == "thread/read":
                return {
                    "thread": {
                        "id": "child",
                        "parentThreadId": "root",
                        "cwd": str(tmp_path),
                        "status": {"type": "active"},
                        "agentNickname": "Mendel",
                    }
                }
            if method == "thread/resume":
                self.subscriptions += 1
                return {}
            if method == "thread/turns/list":
                return {"data": [{"id": "child-turn", "status": "inProgress"}]}
            return {"data": []}

    client = ChildClient()
    spawn = Fact("child", "root", "turn", "spawn", phase="started", child="child")
    await c.consume(client, spawn)
    before = c.runtime.registry.all()
    await c.consume(client, spawn)
    assert c.runtime.registry.all() == before and len(before) == 2
    assert client.subscriptions == 1
    await c.stop()


def test_http_websocket_waiting_context_and_resolution_are_additive(tmp_path: Path) -> None:
    with TestClient(create_app(Settings.for_project(tmp_path))) as client:
        with client.websocket_connect("/ws") as ws:
            assert ws.receive_json()["type"] == "snapshot"
            agent = Agent(id="lead", name="Lead", provider="codex", repository=str(tmp_path))
            client.post(
                "/api/events",
                json={
                    "type": "agent.started",
                    "agent_id": "lead",
                    "payload": {"agent": agent.model_dump(mode="json")},
                },
            )
            assert ws.receive_json()["type"] == "agent.started"
            response = client.post(
                "/api/events",
                json={
                    "type": "agent.state_changed",
                    "agent_id": "lead",
                    "source": "native",
                    "payload": {"to": "waiting", "waiting_reason": "user_input"},
                },
            )
            assert ws.receive_json() == response.json()
            assert client.get("/api/agents/lead").json()["waiting_reason"] == "user_input"
            response = client.post(
                "/api/events",
                json={
                    "type": "agent.state_changed",
                    "agent_id": "lead",
                    "source": "native",
                    "payload": {"to": "idle"},
                },
            )
            assert ws.receive_json() == response.json()
            assert response.json()["changes"]["waiting_reason"] is None


@pytest.mark.asyncio
async def test_reconciliation_item_limit_fails_closed(tmp_path: Path) -> None:
    c = await setup(tmp_path)

    class EndlessClient:
        async def request(self, *_: object) -> dict[str, object]:
            return {
                "data": [{"item": {"type": "userMessage", "text": "private"}}],
                "nextCursor": "more",
            }

    with pytest.raises(NativeUnavailable):
        await c.items(EndlessClient(), "root", "turn")


@pytest.mark.asyncio
async def test_confirmed_child_remains_observable_after_parent_removed(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    c.workspaces["root"] = tmp_path
    c.validation_roots["root"] = (tmp_path,)
    meta = ThreadMetadata("child", tmp_path, "active", "root", "Mendel", None, False)
    await c.adapter.create_child("root", meta)
    await c.runtime.apply(
        AgentEvent(type=AgentEventType.AGENT_STOPPED, source=EventSource.WRAPPER, agent_id="lead")
    )
    assert c.has_live_threads("root") and not c.adapter.live("root")
    await c.validate_workspace(meta, c.bindings.by_thread["child"].office_agent_id)
    await c.adapter.handle(Fact("turn", "child", "child-turn", phase="completed"))
    child_id = c.bindings.by_thread["child"].office_agent_id
    assert c.runtime.registry.get(child_id).status is AgentState.DONE
    assert c.runtime.registry.get(child_id).parent_agent_id == "lead"
    await asyncio.sleep(0.15)
    assert not c.has_live_threads("root")
    await c.stop()


@pytest.mark.asyncio
async def test_snapshot_discards_sensitive_content_and_completed_commands(tmp_path: Path) -> None:
    c = await setup(tmp_path)

    class HistoryClient:
        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            if method == "thread/read":
                return {
                    "thread": {"id": "root", "cwd": str(tmp_path), "status": {"type": "active"}}
                }
            if method == "thread/turns/list":
                return {"data": [{"id": "turn", "status": "inProgress"}]}
            return {
                "data": [
                    {"item": {"type": "userMessage", "id": "q", "text": "sk-private"}},
                    {
                        "item": {
                            "type": "commandExecution",
                            "id": "tool",
                            "command": "pytest",
                            "status": "completed",
                            "aggregatedOutput": "private output",
                        }
                    },
                ]
            }

    facts = await c.items(HistoryClient(), "root", "turn")
    assert len(facts) == 1 and facts[0].phase == "finish"
    assert "private" not in repr(facts)
    await c.hydrate_thread(HistoryClient(), "root")
    await c.adapter.handle(
        Fact(
            "command", "root", "turn", "tool", phase="start", state=AgentState.TESTING, tool="test"
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


@pytest.mark.asyncio
async def test_transport_negotiates_and_never_replies_to_server_request(tmp_path: Path) -> None:
    import json

    from websockets.asyncio.server import unix_serve

    written: list[dict[str, Any]] = []
    seen: asyncio.Queue[Fact] = asyncio.Queue()

    async def receive(value: dict[str, Any]) -> None:
        if fact := parse_event(value, tmp_path):
            seen.put_nowait(fact)

    async def server(socket: Any) -> None:
        async for line in socket:
            value = json.loads(line)
            written.append(value)
            if value.get("method") == "initialize":
                await socket.send(
                    json.dumps(
                        {
                            "id": value["id"],
                            "result": {
                                "userAgent": "codex-tui/0.160.1 (fixture)",
                            },
                        }
                    )
                )
            elif value.get("method") == "thread/read":
                await socket.send(json.dumps({"id": value["id"], "result": {"thread": {}}}))
                await socket.send(
                    json.dumps(
                        {
                            "id": 42,
                            "method": "item/tool/requestUserInput",
                            "params": {
                                "threadId": "root",
                                "turnId": "turn",
                                "itemId": "question",
                                "questions": [{"question": "sk-private"}],
                            },
                        }
                    )
                )

    path = tmp_path / "daemon.sock"
    async with unix_serve(server, path=path):
        async with ReadOnlyClient(path, "0.160.1", receive) as client:
            await client.request("thread/read", {"threadId": "root", "includeTurns": False})
            fact = await asyncio.wait_for(seen.get(), timeout=1)
            assert fact.kind == "request" and "private" not in repr(fact)
            await asyncio.sleep(0.05)
        assert all("method" in value for value in written)
        assert [value["method"] for value in written] == [
            "initialize",
            "initialized",
            "thread/read",
        ]


@pytest.mark.asyncio
async def test_unknown_version_does_not_open_transport(tmp_path: Path) -> None:
    async def ignore(_: dict[str, Any]) -> None:
        pass

    with pytest.raises(NativeUnavailable, match="Unsupported"):
        async with ReadOnlyClient(tmp_path / "not-present", "99.0.0", ignore):
            pass


@pytest.mark.asyncio
async def test_handshake_version_mismatch_fails_without_subscribing(tmp_path: Path) -> None:
    import json

    from websockets.asyncio.server import unix_serve

    methods: list[str] = []

    async def ignore(_: dict[str, Any]) -> None:
        pass

    async def server(socket: Any) -> None:
        async for line in socket:
            value = json.loads(line)
            methods.append(value["method"])
            await socket.send(
                json.dumps(
                    {
                        "id": value["id"],
                        "result": {
                            "userAgent": "codex-tui/99.0.0 (fixture)",
                        },
                    }
                )
            )

    path = tmp_path / "daemon.sock"
    async with unix_serve(server, path=path):
        with pytest.raises(NativeUnavailable, match="mismatch"):
            async with ReadOnlyClient(path, "0.160.1", ignore):
                pass
    assert methods == ["initialize"]


@pytest.mark.asyncio
async def test_native_file_completion_restores_live_tool_fallback(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    tool = AgentEvent(
        type=AgentEventType.TOOL_STARTED,
        source=EventSource.TOOL_PROCESS,
        agent_id="lead",
        payload={"command": "pytest", "tool": "test"},
    )
    await c.runtime.apply(tool)
    edit = Fact("file", "root", "turn", "edit", phase="start")
    await c.adapter.handle(edit)
    assert c.runtime.registry.get("lead").status is AgentState.CODING
    # Rejected fallback evidence remains private and cannot interrupt native coding.
    await c.runtime.apply(
        tool.model_copy(update={"timestamp": c.runtime.registry.get("lead").last_active_at})
    )
    await c.adapter.handle(replace(edit, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    assert c.runtime.status_evidence("lead").source is EventSource.TOOL_PROCESS
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.STATE_CHANGED,
            source=EventSource.TIMEOUT,
            agent_id="lead",
            payload={"to": "idle"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_FINISHED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"next_state": "thinking"},
        )
    )
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


@pytest.mark.asyncio
async def test_finished_fallback_is_not_revived_after_native_wait(tmp_path: Path) -> None:
    c = await setup(tmp_path)
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"command": "pytest", "tool": "test"},
        )
    )
    await c.adapter.handle(Fact("request", "root", "turn", "question", "request"))
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_FINISHED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            payload={"next_state": "thinking"},
        )
    )
    assert c.runtime.registry.get("lead").waiting_reason == "user_input"
    await c.adapter.handle(Fact("resolved", "root", request="request"))
    assert c.runtime.registry.get("lead").status is AgentState.THINKING


@pytest.mark.asyncio
async def test_delayed_fallback_completion_reconciles_handoff_without_rewinding_time(
    tmp_path: Path,
) -> None:
    from datetime import timedelta

    from backend.models import utc_now

    c = await setup(tmp_path)
    observed = utc_now()
    await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            source=EventSource.TOOL_PROCESS,
            agent_id="lead",
            timestamp=observed,
            payload={"command": "pytest", "tool": "test"},
        )
    )
    edit = Fact("file", "root", "turn", "edit", phase="start")
    await c.adapter.handle(edit)
    # The process scan finished before the native release but hasn't been applied yet.
    finish = AgentEvent(
        type=AgentEventType.TOOL_FINISHED,
        source=EventSource.TOOL_PROCESS,
        agent_id="lead",
        timestamp=observed + timedelta(microseconds=1),
        payload={"next_state": "thinking"},
    )
    await c.adapter.handle(replace(edit, phase="finish"))
    assert c.runtime.registry.get("lead").status is AgentState.TESTING
    floor = c.runtime.status_evidence("lead").observed_at
    assert finish.timestamp < floor
    await c.runtime.apply(finish)
    assert c.runtime.registry.get("lead").status is AgentState.THINKING
    assert c.runtime.status_evidence("lead").observed_at == floor
    assert c.runtime.registry.get("lead").last_active_at >= floor
    # Older unrelated status updates still fail the original global recency rule.
    response = await c.runtime.apply(
        AgentEvent(
            type=AgentEventType.STATE_CHANGED,
            source=EventSource.NATIVE,
            agent_id="lead",
            timestamp=observed,
            payload={"to": "coding"},
        )
    )
    assert response["changes"] == {}
