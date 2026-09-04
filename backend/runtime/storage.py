import json
from collections.abc import Iterable
from pathlib import Path

from backend.models import AgentEvent


class EventStorage:
    """Append-only JSONL event log used for recovery, debug, and replay."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, event: AgentEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(event.model_dump_json() + "\n")

    def read(self) -> list[AgentEvent]:
        if not self.path.exists():
            return []
        events: list[AgentEvent] = []
        with self.path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    events.append(AgentEvent.model_validate_json(line))
                except (ValueError, json.JSONDecodeError) as error:
                    raise ValueError(f"Invalid event at {self.path}:{line_number}") from error
        return events

    def replace(self, events: Iterable[AgentEvent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        content = "".join(event.model_dump_json() + "\n" for event in events)
        self.path.write_text(content, encoding="utf-8")
