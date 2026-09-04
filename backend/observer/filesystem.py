import hashlib
import os
from pathlib import Path

from backend.models import AgentEvent, AgentEventType

IGNORED_DIRECTORIES = {".git", ".venv", "node_modules", "dist", "build", "__pycache__"}


class FileSystemObserver:
    """Poll a repository and emit normalized events for changed source files."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()
        self._snapshot: dict[str, str] | None = None

    def scan(self, agent_id: str) -> list[AgentEvent]:
        current = self._read_snapshot()
        if self._snapshot is None:
            self._snapshot = current
            return []

        changed = sorted(
            path
            for path, digest in current.items()
            if self._snapshot.get(path) != digest
        )
        removed = sorted(set(self._snapshot) - set(current))
        self._snapshot = current
        return [
            AgentEvent(
                type=AgentEventType.FILE_CHANGED,
                agent_id=agent_id,
                payload={"file": path, "deleted": path in removed},
            )
            for path in [*changed, *removed]
        ]

    def _read_snapshot(self) -> dict[str, str]:
        snapshot: dict[str, str] = {}
        if not self.path.exists():
            return snapshot
        for root, directories, filenames in os.walk(self.path):
            directories[:] = sorted(set(directories) - IGNORED_DIRECTORIES)
            for filename in filenames:
                path = Path(root, filename)
                try:
                    relative = path.relative_to(self.path).as_posix()
                    digest = hashlib.blake2s(path.read_bytes(), digest_size=8).hexdigest()
                except (OSError, ValueError):
                    continue
                snapshot[relative] = digest
        return snapshot
