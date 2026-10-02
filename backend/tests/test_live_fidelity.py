"""Real local process smoke test; no model calls or external credentials required."""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from backend.adapters.generic import GenericProcessAdapter
from backend.api.app import create_app
from backend.cli import run_wrapped
from backend.config import Settings
from backend.models import AgentEvent, AgentEventType


def test_wrapped_live_process_search_testing_idle_protection_and_cleanup(tmp_path: Path) -> None:
    worker = tmp_path / "worker.py"
    worker.write_text(
        """import subprocess
import sys
import time
from pathlib import Path

search = subprocess.Popen(["rg", "symbol"], stdin=subprocess.PIPE)
Path("search-ready").touch()
while not Path("run-tests").exists():
    time.sleep(0.01)
search.terminate()
search.wait(timeout=5)
tests = subprocess.Popen([sys.executable, "-m", "pytest", "-q", "test_live.py"])
assert tests.wait(timeout=15) == 0
while not Path("exit-worker").exists():
    time.sleep(0.01)
""",
        encoding="utf-8",
    )
    (tmp_path / "test_live.py").write_text(
        """import time
from pathlib import Path

def test_controlled_activity():
    Path("testing-ready").touch()
    deadline = time.monotonic() + 10
    while not Path("finish-tests").exists():
        assert time.monotonic() < deadline
        time.sleep(0.01)
""",
        encoding="utf-8",
    )
    settings = Settings.for_project(tmp_path)
    settings.observer.enabled = True
    settings.observer.idle_timeout = 0.02
    settings.observer.scan_interval = 0.01
    settings.observer.tool_scan_interval = 0.01
    app = create_app(settings)
    adapter = GenericProcessAdapter(pids=[], scan_interval=0.01)
    app.state.observer.adapters = [adapter]

    with TestClient(app) as client, ThreadPoolExecutor(max_workers=1) as executor:

        def emit(event: AgentEvent) -> None:
            response = client.post("/api/events", json=event.model_dump(mode="json"))
            # Process cleanup can win the race with the wrapper's final DONE update.
            # HttpEventEmitter drops that 404; other event failures are still unexpected.
            late_completion = (
                event.type is AgentEventType.STATE_CHANGED
                and event.payload.get("to") == "done"
                and response.status_code == 404
            )
            assert response.status_code == 200 or late_completion, response.text
            if (
                event.type is AgentEventType.STATE_CHANGED
                and event.payload.get("from") == "starting"
            ):
                # Start passive observation after registration's initial baseline update.
                adapter.processes.pids = [client.get("/api/agents/smoke-worker").json()["pid"]]

        future = executor.submit(
            run_wrapped,
            [sys.executable, str(worker)],
            name="Smoke Worker",
            provider="custom",
            repository=tmp_path,
            role="Backend",
            task="Smoke test",
            emitter=emit,
            agent_id="smoke-worker",
        )

        def wait_for_status(status: str) -> None:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                agents = client.get("/api/agents").json()
                if agents and agents[0]["status"] == status:
                    assert len(agents) == 1
                    assert agents[0]["id"] == "smoke-worker"
                    assert agents[0]["name"] == "Smoke Worker"
                    return
                time.sleep(0.01)
            raise AssertionError(f"Did not observe {status}")

        try:
            wait_for_status("searching")
            (tmp_path / "run-tests").touch()
            wait_for_status("testing")
            # Keep checking for far longer than the idle threshold while pytest is alive.
            deadline = time.monotonic() + 0.2
            while time.monotonic() < deadline:
                assert client.get("/api/agents/smoke-worker").json()["status"] == "testing"
                time.sleep(0.01)
        finally:
            for gate in ["run-tests", "finish-tests", "exit-worker"]:
                (tmp_path / gate).touch()
            assert future.result(timeout=15) == 0
        assert client.get("/api/agents").json() == []
