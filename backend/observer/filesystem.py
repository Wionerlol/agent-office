from pathlib import Path
from queue import Empty, Queue

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer as WatchdogObserver

from backend.models import AgentEvent, AgentEventType

IGNORED_DIRECTORIES = frozenset(
    {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}
)


class _EventHandler(FileSystemEventHandler):
    def __init__(self, root: Path, events: Queue[tuple[str, bool]]) -> None:
        super().__init__()
        self.root = root
        self.events = events

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        try:
            relative = Path(event.src_path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return
        if any(part in IGNORED_DIRECTORIES for part in Path(relative).parts):
            return
        self.events.put((relative, event.event_type == "deleted"))


class FileSystemObserver:
    """Use watchdog to drain native filesystem changes as normalized events."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()
        self._events: Queue[tuple[str, bool]] = Queue()
        self._observer: WatchdogObserver | None = None

    def scan(self, agent_id: str) -> list[AgentEvent]:
        if self._observer is None:
            self._start()
        changes: dict[str, bool] = {}
        while True:
            try:
                path, deleted = self._events.get_nowait()
            except Empty:
                break
            changes[path] = deleted
        return [
            AgentEvent(
                type=AgentEventType.FILE_CHANGED,
                agent_id=agent_id,
                payload={"file": path, "deleted": deleted},
            )
            for path, deleted in sorted(changes.items())
        ]

    def close(self) -> None:
        if self._observer is None:
            return
        self._observer.stop()
        self._observer.join(timeout=2)
        self._observer = None

    def _start(self) -> None:
        if not self.path.is_dir():
            return
        observer = WatchdogObserver()
        handler = _EventHandler(self.path, self._events)
        observer.schedule(handler, str(self.path), recursive=True)
        try:
            observer.start()
        except Exception:
            observer.stop()
            if observer.is_alive():
                observer.join(timeout=2)
            raise
        else:
            self._observer = observer
