"""One deterministic policy for native concurrency and bounded replay memory."""

from collections import OrderedDict
from dataclasses import dataclass, field

from backend.models import AgentState
from backend.native.codex.protocol import Fact


class ReplayCache:
    def __init__(self, capacity: int = 8192) -> None:
        self.capacity = capacity
        self.entries: OrderedDict[tuple[object, ...], None] = OrderedDict()

    def add(self, key: tuple[object, ...]) -> bool:
        if key in self.entries:
            self.entries.move_to_end(key)
            return False
        self.entries[key] = None
        if len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return True


@dataclass
class Activity:
    commands: dict[tuple[str | None, str | None], Fact] = field(default_factory=dict)
    files: set[tuple[str | None, str | None]] = field(default_factory=set)
    requests: set[str] = field(default_factory=set)
    waits: dict[tuple[str | None, str | None], str] = field(default_factory=dict)
    waiting_flag: bool = False
    idle: bool = False
    terminal: AgentState | None = None
    terminal_turn: str | None = None
    latest_turn: str | None = None

    def clear_active(self) -> None:
        self.commands.clear()
        self.files.clear()
        self.requests.clear()
        self.waits.clear()
        self.waiting_flag = False

    def derive(self) -> tuple[AgentState, str | None, str | None, str | None, bool]:
        if self.terminal:
            return self.terminal, None, None, None, False
        if self.requests or self.waiting_flag:
            return AgentState.WAITING, None, "user_input", None, False
        if self.waits:
            return AgentState.WAITING, None, "child_agent", next(iter(self.waits.values())), False
        commands = list(self.commands.values())
        for state in (AgentState.TESTING, AgentState.SEARCHING):
            if command := next((x for x in commands if x.state == state), None):
                return state, command.tool, None, None, False
        if self.files:
            return AgentState.CODING, None, None, None, False
        if commands:
            return AgentState.TOOL_RUNNING, commands[0].tool, None, None, False
        return (
            (AgentState.IDLE if self.idle else AgentState.THINKING),
            None,
            None,
            None,
            not self.idle,
        )
