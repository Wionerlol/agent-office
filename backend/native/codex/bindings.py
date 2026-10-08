"""Explicit, sticky, bounded bindings for one OfficeRuntime lifetime."""

import re
from dataclasses import dataclass
from datetime import UTC, datetime


def same_generation(started_at: datetime, generation: str) -> bool:
    """Compare exact instants, rejecting ambiguous or lossy generation timestamps.

    Accept explicit ISO date/time with seconds, up to microsecond precision and
    Z or a numeric timezone offset. -00:00 denotes an unknown offset, not UTC.
    Never assume the local timezone for a naive registered instance or request.
    """
    if (
        started_at.utcoffset() is None
        or generation.endswith("-00:00")
        or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)",
            generation,
        )
    ):
        return False
    try:
        expected = datetime.fromisoformat(generation)
        return started_at.astimezone(UTC) == expected.astimezone(UTC)
    except (ValueError, OverflowError):
        return False


class BindingConflict(ValueError):
    pass


@dataclass(frozen=True)
class NativeThreadBinding:
    office_agent_id: str
    thread_id: str
    root_thread_id: str
    generation: str
    child_definition_id: str | None = None
    parent_thread_id: str | None = None


class BindingRegistry:
    def __init__(self, capacity: int = 1024) -> None:
        self.capacity = capacity
        self.by_thread: dict[str, NativeThreadBinding] = {}
        self.by_agent: dict[str, NativeThreadBinding] = {}

    def check(self, binding: NativeThreadBinding) -> None:
        for previous in (
            self.by_thread.get(binding.thread_id),
            self.by_agent.get(binding.office_agent_id),
        ):
            if previous is not None and previous != binding:
                raise BindingConflict("Agent/thread already bound for this runtime session")
        if binding.thread_id not in self.by_thread and len(self.by_thread) >= self.capacity:
            raise BindingConflict("Native binding capacity reached; restart the office session")

    def add(self, binding: NativeThreadBinding) -> None:
        self.check(binding)
        self.by_thread[binding.thread_id] = binding
        self.by_agent[binding.office_agent_id] = binding
