from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    command: list[str]
    cwd: str
    created_at: float
    environment: dict[str, str]


class ProcessObserver:
    """Safely read process facts used by provider adapters."""

    def __init__(self, pids: list[int] | None = None) -> None:
        self.pids = pids

    def snapshots(self) -> list[ProcessSnapshot]:
        processes = (
            [psutil.Process(pid) for pid in self.pids]
            if self.pids is not None
            else psutil.process_iter()
        )
        snapshots: list[ProcessSnapshot] = []
        for process in processes:
            try:
                command = process.cmdline()
                if not command:
                    continue
                snapshots.append(
                    ProcessSnapshot(
                        pid=process.pid,
                        command=command,
                        cwd=process.cwd() or str(Path.cwd()),
                        created_at=process.create_time(),
                        environment=process.environ(),
                    )
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return snapshots
