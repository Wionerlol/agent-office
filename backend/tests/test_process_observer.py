import psutil
import pytest

from backend.observer.process import ProcessObserver


def test_global_scan_skips_unrelated_process_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class UnrelatedProcess:
        pid = 123

        def cmdline(self) -> list[str]:
            return ["postgres"]

        def cwd(self) -> str:
            raise AssertionError("cwd should not be read for unrelated processes")

        def create_time(self) -> float:
            raise AssertionError("create_time should not be read for unrelated processes")

        def environ(self) -> dict[str, str]:
            raise AssertionError("environment should not be read for unrelated processes")

    monkeypatch.setattr(psutil, "process_iter", lambda: [UnrelatedProcess()])

    observer = ProcessObserver(command_hints={"codex", "office-run"})

    assert observer.snapshots() == []


def test_global_scan_includes_a_custom_agent_started_by_office_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Process:
        def __init__(self, pid: int, parent: int, command: list[str]) -> None:
            self.pid = pid
            self._parent = parent
            self._command = command

        def cmdline(self) -> list[str]:
            return self._command

        def ppid(self) -> int:
            return self._parent

        def cwd(self) -> str:
            return "/repo"

        def create_time(self) -> float:
            return 0

        def environ(self) -> dict[str, str]:
            return {"AGENT_OFFICE_ID": "custom"} if self.pid == 2 else {}

    processes = [
        Process(1, 0, ["python", "/usr/local/bin/office-run", "my-agent"]),
        Process(2, 1, ["/opt/my-agent"]),
    ]
    monkeypatch.setattr(psutil, "process_iter", lambda: processes)

    snapshots = ProcessObserver(command_hints={"codex", "office-run"}).snapshots()

    assert [snapshot.pid for snapshot in snapshots] == [1, 2]
