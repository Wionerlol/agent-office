import shlex

from backend.models import AgentState

TEST_MARKERS = {
    "pytest",
    "npm test",
    "npm run test",
    "pnpm test",
    "yarn test",
    "cargo test",
    "go test",
    "mvn test",
}
SEARCH_COMMANDS = {"rg", "grep", "find", "fd", "locate"}


def state_for_command(command: str | list[str]) -> AgentState:
    text = command if isinstance(command, str) else shlex.join(command)
    normalized = " ".join(text.lower().split())
    if any(marker in normalized for marker in TEST_MARKERS):
        return AgentState.TESTING
    try:
        executable = shlex.split(normalized)[0].rsplit("/", 1)[-1]
    except (ValueError, IndexError):
        return AgentState.TOOL_RUNNING
    if executable in SEARCH_COMMANDS:
        return AgentState.SEARCHING
    return AgentState.TOOL_RUNNING
