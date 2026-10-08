"""Generation handshakes through real HTTP routes; native reads are isolated fixtures."""

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

import backend.native.codex.consumer as module
import backend.native_cli as cli
from backend.api.app import create_app
from backend.config import Settings
from backend.models import Agent, AgentEvent, AgentEventType, EventSource
from backend.native.codex.bindings import NativeThreadBinding, same_generation
from backend.native.codex.consumer import CodexNativeConsumer

BindingAPI = tuple[TestClient, CodexNativeConsumer, Agent, list[str]]


@pytest.fixture
def binding_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[BindingAPI]:
    settings = Settings.for_project(tmp_path)
    settings.native.codex.enabled = True
    app = create_app(settings)
    native = app.state.native
    reads: list[str] = []

    class Client:
        def __init__(self, *args: Any) -> None:
            pass

        async def __aenter__(self) -> "Client":
            return self

        async def __aexit__(self, *args: Any) -> None:
            pass

        async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
            reads.append(method)
            return {
                "thread": {
                    "id": params["threadId"],
                    "cwd": str(tmp_path),
                    "status": {"type": "idle"},
                }
            }

    async def connection() -> tuple[str, Path]:
        return "0.161.0", tmp_path / "socket"

    async def observe(_: NativeThreadBinding) -> None:
        pass

    monkeypatch.setattr(module, "ReadOnlyClient", Client)
    monkeypatch.setattr(native, "connection_info", connection)
    monkeypatch.setattr(native, "_run", observe)
    agent = Agent(
        id="lead",
        name="Lead",
        provider="codex",
        repository=str(tmp_path),
        started_at=datetime(2026, 10, 9, 1, 2, 3, 123456, tzinfo=UTC),
    )
    with TestClient(app) as client:
        event = AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            source=EventSource.WRAPPER,
            agent_id=agent.id,
            payload={"agent": agent.model_dump(mode="json")},
        )
        assert client.post("/api/events", json=event.model_dump(mode="json")).status_code == 200
        yield client, native, agent, reads


@pytest.mark.parametrize("suffix", ["Z", "+00:00", "+08:00"])
def test_equivalent_generation_instants_bind(binding_api: BindingAPI, suffix: str) -> None:
    client, native, agent, _ = binding_api
    generation = (
        "2026-10-09T09:02:03.123456" if suffix == "+08:00" else "2026-10-09T01:02:03.123456"
    )
    response = client.post(
        "/api/native/codex/bind",
        json={
            "office_agent_id": "lead",
            "thread_id": str(uuid4()),
            "expected_generation": generation + suffix,
        },
    )
    assert response.status_code == 200, response.text
    assert native.adapter.live(response.json()["thread_id"]) is not None
    assert native.runtime.registry.get("lead").started_at == agent.started_at


@pytest.mark.parametrize(
    "generation",
    [
        "2026-10-09T01:02:03.123455Z",  # Different instance by one microsecond.
        "2026-10-09T01:02:03.123456+08:00",  # Same clock, different instant.
        "not-a-timestamp",
        "2026-10-09",
        "2026-10-09T01:02:03.123456",
        "2026-10-09T01:02:03.123456-00:00",  # Unknown offset, not explicit UTC.
        "2026-10-09T01:02:03.1234567Z",  # Must not silently truncate generation precision.
        "2026-10-09 01:02:03.123456Z",
        "2026-10-09T01:02:03+25:00",
        "2026-10-09T01:02:03.123456+00:60",
        "2026-02-30T01:02:03.123456Z",
    ],
)
def test_invalid_or_stale_generation_fails_before_native_read(
    binding_api: BindingAPI, generation: str
) -> None:
    client, native, _, reads = binding_api
    response = client.post(
        "/api/native/codex/bind",
        json={
            "office_agent_id": "lead",
            "thread_id": str(uuid4()),
            "expected_generation": generation,
        },
    )
    assert response.status_code == 409
    assert not reads and not native.bindings.by_thread


@pytest.mark.parametrize("mode", ["manual", "resume"])
def test_cli_and_explicit_resume_use_registered_generation(
    binding_api: BindingAPI,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
) -> None:
    client, native, agent, _ = binding_api
    thread = str(uuid4())
    posts: list[httpx.Response] = []

    def respond(request: httpx.Request) -> httpx.Response:
        response = client.request(
            request.method,
            request.url.path,
            json=json.loads(request.content) if request.content else None,
        )
        result = httpx.Response(response.status_code, json=response.json())
        if request.method == "POST":
            posts.append(result)
        return result

    original = httpx.Client
    monkeypatch.setattr(
        cli.httpx,
        "Client",
        lambda **kwargs: original(transport=httpx.MockTransport(respond), **kwargs),
    )
    if mode == "manual":
        assert client.get("/api/agents/lead").json()["started_at"].endswith("Z")
        cli.main(["--server", "http://127.0.0.1:8000", "bind", "lead", thread])
        assert "lead" in capsys.readouterr().out
    else:
        selected = cli.explicit_thread(["codex", "resume", thread], None)
        cli.BindingHandshake("http://127.0.0.1:8000", selected)._bind(agent)
    assert len(posts) == 1 and posts[0].status_code == 200
    assert native.bindings.by_agent["lead"].thread_id == thread


def test_existing_binding_does_not_attach_to_reused_office_id(binding_api: BindingAPI) -> None:
    client, native, agent, _ = binding_api
    thread = str(uuid4())
    payload = {
        "office_agent_id": "lead",
        "thread_id": thread,
        "expected_generation": agent.model_dump(mode="json")["started_at"],
    }
    assert client.post("/api/native/codex/bind", json=payload).status_code == 200
    # Simulate an independently registered replacement instance with the same Office ID.
    native.runtime.registry.get("lead").started_at = agent.started_at + timedelta(microseconds=1)
    assert native.adapter.live(thread) is None
    assert client.post("/api/native/codex/bind", json=payload).status_code == 409


def test_naive_registered_generation_is_not_assumed_utc() -> None:
    assert not same_generation(datetime(2026, 10, 9, 1, 2, 3), "2026-10-09T01:02:03Z")
    assert not same_generation(datetime.now(UTC), "")


def test_legacy_bind_can_omit_expected_generation(binding_api: BindingAPI) -> None:
    client, _, _, _ = binding_api
    assert (
        client.post(
            "/api/native/codex/bind",
            json={
                "office_agent_id": "lead",
                "thread_id": str(uuid4()),
            },
        ).status_code
        == 200
    )
