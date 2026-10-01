import os
import subprocess

import pytest

from backend.models import AgentEventType, AgentState, EventSource
from backend.observer.tools import ToolObserver


def test_tool_observer_tracks_real_child_processes() -> None:
    observer = ToolObserver()
    child = subprocess.Popen(["sleep", "10"])
    try:
        started = observer.scan("worker", os.getpid())
        assert any(
            event.type is AgentEventType.TOOL_STARTED and event.payload["tool"] == "sleep"
            for event in started
        )
        assert all(event.source is EventSource.TOOL_PROCESS for event in started)
    finally:
        child.terminate()
        child.wait(timeout=5)

    finished = observer.scan("worker", os.getpid())
    assert any(event.type is AgentEventType.TOOL_FINISHED for event in finished)
    assert all(event.source is EventSource.TOOL_PROCESS for event in finished)


def test_concurrent_tools_keep_the_strongest_live_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psutil

    class Child:
        def __init__(self, pid: int, command: list[str]) -> None:
            self.pid = pid
            self.command = command

        def cmdline(self) -> list[str]:
            return self.command

    children = [Child(1, ["pytest"]), Child(2, ["rg", "symbol"])]

    class Root:
        def children(self, recursive: bool) -> list[Child]:
            return children

    monkeypatch.setattr(psutil, "Process", lambda _: Root())
    observer = ToolObserver()
    started = observer.scan("worker", 100)
    assert all(item.payload["next_state"] is AgentState.TESTING for item in started)
    assert {tuple(item.payload["command"]) for item in started} == {("pytest",), ("rg", "symbol")}
    children.pop(1)
    finished = observer.scan("worker", 100)
    assert finished[0].payload["next_state"] is AgentState.TESTING
    assert finished[0].payload["next_tool"] == "test"
    children.clear()
    assert observer.scan("worker", 100)[0].payload["next_state"] is AgentState.THINKING


def test_tool_exec_changes_and_permission_failures_preserve_activity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psutil

    class Child:
        pid = 1
        command = ["bash", "-c", "sleep 1"]
        denied = False

        def cmdline(self) -> list[str]:
            if self.denied:
                raise psutil.AccessDenied(self.pid)
            return self.command

    child = Child()

    class Root:
        def children(self, recursive: bool) -> list[Child]:
            return [child]

    monkeypatch.setattr(psutil, "Process", lambda _: Root())
    observer = ToolObserver()
    observer.scan("worker", 100)
    child.command = ["pytest"]
    events = observer.scan("worker", 100)
    assert events[-1].type is AgentEventType.TOOL_STARTED
    assert events[-1].payload["next_state"] is AgentState.TESTING
    child.denied = True
    assert observer.scan("worker", 100) == []


@pytest.mark.parametrize(
    "launcher",
    [
        ["/vendor/codex", "exec", "Run pytest and rg"],
        ["node", "/usr/bin/codex", "exec", "Run pytest and rg"],
    ],
)
def test_agent_launcher_prompt_is_not_tool_activity(
    launcher: list[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import psutil

    class Child:
        pid = 1

        def cmdline(self) -> list[str]:
            return launcher

    class Root:
        def children(self, recursive: bool) -> list[Child]:
            return [Child()]

    monkeypatch.setattr(psutil, "Process", lambda _: Root())
    assert ToolObserver().scan("worker", 100) == []
