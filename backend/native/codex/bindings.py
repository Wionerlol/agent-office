"""Explicit, sticky, bounded bindings for one OfficeRuntime lifetime."""

from dataclasses import dataclass


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
