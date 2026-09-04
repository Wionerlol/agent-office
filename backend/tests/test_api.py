from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import Settings
from backend.models import Agent


def test_rest_and_websocket_expose_the_same_live_agents(tmp_path):
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
        assert client.get("/api/agents").json()[0]["id"] == "frontend"
        assert client.get("/api/agents/frontend").json()["status"] == "coding"
        project = client.get("/api/project").json()
        assert project["path"] == str(tmp_path)

        with client.websocket_connect("/ws") as websocket:
            snapshot = websocket.receive_json()
            assert snapshot["type"] == "snapshot"
            assert snapshot["agents"][0]["id"] == "frontend"
