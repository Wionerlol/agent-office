import re
import shlex

import psutil

from backend.models import AgentEvent, AgentEventType, AgentState

TEST_MARKERS = frozenset(
    {
        "pytest",
        "npm test",
        "npm run test",
        "pnpm test",
        "yarn test",
        "cargo test",
        "go test",
        "mvn test",
    }
)
BUILD_MARKERS = (
    "npm run build",
    "pnpm build",
    "yarn build",
    "cargo build",
    "go build",
    "mvn package",
)
LINT_MARKERS = ("ruff ", "eslint", "npm run lint", "pnpm lint", "yarn lint")
SHELL_COMMANDS = frozenset({"sh", "bash", "zsh", "fish", "pwsh"})


def tool_kind(command: str | list[str]) -> str:
    text = command if isinstance(command, str) else shlex.join(command)
    normalized = " ".join(text.lower().split())
    if any(marker in normalized for marker in TEST_MARKERS):
        return "test"
    if re.search(r"(?:^|[\s'\";&|])(?:rg|grep|find|fd|locate)(?=[\s'\";&|]|$)", normalized):
        return "search"
    if re.search(r"(?:^|[\s'\";&|])git(?=[\s'\";&|]|$)", normalized):
        return "git"
    if any(marker in normalized for marker in BUILD_MARKERS):
        return "build"
    if any(marker in normalized for marker in LINT_MARKERS):
        return "lint"
    try:
        executable = shlex.split(normalized)[0].rsplit("/", 1)[-1]
    except (ValueError, IndexError):
        return "tool"
    if executable in SHELL_COMMANDS:
        return "shell"
    return executable


def state_for_command(command: str | list[str]) -> AgentState:
    kind = tool_kind(command)
    if kind == "test":
        return AgentState.TESTING
    if kind == "search":
        return AgentState.SEARCHING
    return AgentState.TOOL_RUNNING


class ToolObserver:
    """Detect commands spawned beneath an agent process and emit their lifecycles."""

    def __init__(self) -> None:
        self._active: dict[str, dict[int, list[str]]] = {}

    def scan(self, agent_id: str, root_pid: int) -> list[AgentEvent]:
        previous = self._active.get(agent_id, {})
        current: dict[int, list[str]] = {}
        try:
            children = psutil.Process(root_pid).children(recursive=True)
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            children = []
        for process in children:
            try:
                command = process.cmdline()
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            if command:
                current[process.pid] = command

        events = [
            AgentEvent(
                type=AgentEventType.TOOL_STARTED,
                agent_id=agent_id,
                payload={"tool": tool_kind(command), "command": command, "pid": pid},
            )
            for pid, command in current.items()
            if pid not in previous
        ]
        events.extend(
            AgentEvent(
                type=AgentEventType.TOOL_FINISHED,
                agent_id=agent_id,
                payload={"tool": tool_kind(command), "pid": pid},
            )
            for pid, command in previous.items()
            if pid not in current
        )
        self._active[agent_id] = current
        return events

    def forget(self, agent_id: str) -> None:
        self._active.pop(agent_id, None)
