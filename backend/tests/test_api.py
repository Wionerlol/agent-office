from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import Settings
from backend.models import Agent, AgentEvent, AgentEventType


def test_rest_and_websocket_expose_the_same_live_agents(tmp_path: Path) -> None:
    settings = Settings.for_project(tmp_path)
    app = create_app(settings)
    agent = Agent(
        id="frontend",
        name="Frontend",
        provider="test",
        repository=str(tmp_path),
        status="coding",
        started_at=datetime.now(UTC),
        last_active_at=datetime.now(UTC),
    )
    app.state.runtime.registry.add(agent)

    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/guide").status_code == 200
        assert client.get("/api/agents").json()[0]["id"] == "frontend"
        assert client.get("/api/agents/frontend").json()["status"] == "coding"
        project = client.get("/api/project").json()
        assert project["path"] == str(tmp_path)
        assert client.get("/api/config").json() == {"desks": 8}

        with client.websocket_connect("/ws") as websocket:
            snapshot = websocket.receive_json()
            assert snapshot["type"] == "snapshot"
            assert snapshot["agents"][0]["id"] == "frontend"


def test_app_ignores_stale_runtime_history(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "events.jsonl").write_text("not valid json\n", encoding="utf-8")

    with TestClient(create_app(Settings.for_project(tmp_path))) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_live_events_are_not_persisted_to_disk(tmp_path: Path) -> None:
    agent = Agent(
        id="live",
        name="Live Agent",
        provider="test",
        repository=str(tmp_path),
        status="starting",
    )

    with TestClient(create_app(Settings.for_project(tmp_path))) as client:
        response = client.post(
            "/api/events",
            json=AgentEvent(
                type=AgentEventType.AGENT_STARTED,
                agent_id="live",
                payload={"agent": agent.model_dump(mode="json")},
            ).model_dump(mode="json"),
        )

    assert response.status_code == 200
    assert not (tmp_path / "runtime" / "events.jsonl").exists()
