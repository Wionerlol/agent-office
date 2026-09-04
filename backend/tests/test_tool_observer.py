import os
import subprocess

from backend.models import AgentEventType
from backend.observer.tools import ToolObserver


def test_tool_observer_tracks_real_child_processes() -> None:
    observer = ToolObserver()
    child = subprocess.Popen(["sleep", "10"])
    try:
        started = observer.scan("worker", os.getpid())
        assert any(
            event.type is AgentEventType.TOOL_STARTED
            and event.payload["tool"] == "sleep"
            for event in started
        )
    finally:
        child.terminate()
        child.wait(timeout=5)

    finished = observer.scan("worker", os.getpid())
    assert any(event.type is AgentEventType.TOOL_FINISHED for event in finished)
