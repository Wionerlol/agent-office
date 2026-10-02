from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    parent_pid: int
    command: list[str]
    cwd: str
    created_at: float
    environment: dict[str, str]


class ProcessObserver:
    """Safely read process facts used by provider adapters."""

    def __init__(
        self,
        pids: list[int] | None = None,
        command_hints: set[str] | None = None,
    ) -> None:
        self.pids = pids
        self.command_hints = command_hints

    def snapshots(self) -> list[ProcessSnapshot]:
        if self.pids is None:
            processes = list(psutil.process_iter())
        else:
            processes = []
            for pid in self.pids:
                try:
                    processes.append(psutil.Process(pid))
                except psutil.NoSuchProcess:
                    continue
        candidates: list[tuple[psutil.Process, list[str], set[str]]] = []
        for process in processes:
            try:
                command = process.cmdline()
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            if command:
                candidates.append((process, command, {Path(part).name.lower() for part in command}))

        wrapper_pids = {process.pid for process, _, names in candidates if "office-run" in names}
        snapshots: list[ProcessSnapshot] = []
        for process, command, command_names in candidates:
            if self.command_hints and command_names.isdisjoint(self.command_hints):
                if not wrapper_pids:
                    continue
                try:
                    if process.ppid() not in wrapper_pids:
                        continue
                except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                    continue
            try:
                snapshots.append(
                    ProcessSnapshot(
                        pid=process.pid,
                        parent_pid=process.ppid(),
                        command=command,
                        cwd=process.cwd() or str(Path.cwd()),
                        created_at=process.create_time(),
                        environment=process.environ(),
                    )
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
        return snapshots
