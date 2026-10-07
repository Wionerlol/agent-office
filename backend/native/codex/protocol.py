"""Version gates and content-free facts from the confirmed Codex protocol subset."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.models import AgentState
from backend.observer.tools import state_for_command

# Exact reviewed versions, not a guess about future experimental protocol compatibility.
SUPPORTED_VERSIONS = frozenset({"0.159.3", "0.160.0", "0.160.1"})
READ_METHODS = frozenset(
    {"initialize", "thread/read", "thread/resume", "thread/turns/list", "thread/items/list"}
)


class NativeUnavailable(RuntimeError):
    pass


def require_version(version: str) -> None:
    if version not in SUPPORTED_VERSIONS:
        raise NativeUnavailable("Unsupported Codex app-server version")


def identifier(value: object) -> str | None:
    return value if isinstance(value, str) and 0 < len(value) <= 200 else None


def nickname(value: object) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"[\w .-]{1,80}", value):
        if not re.search(r"(?i)(sk-|gh[pousr]_|secret|password|bearer)", value):
            return value
    return None


def scoped_path(value: object, workspace: Path) -> str | None:
    if not isinstance(value, str) or len(value) > 4096:
        return None
    candidate = Path(value)
    candidate = candidate if candidate.is_absolute() else workspace / candidate
    try:
        result = candidate.resolve().relative_to(workspace.resolve()).as_posix()
    except (ValueError, OSError):
        return None
    if len(result) > 200 or re.search(r"(?i)(sk-|gh[pousr]_|password|secret)", result):
        return None
    return result


@dataclass(frozen=True)
class Fact:
    kind: str
    thread: str
    turn: str | None = None
    item: str | None = None
    request: str | None = None
    phase: str | None = None
    child: str | None = None
    state: AgentState | None = None
    tool: str | None = None
    paths: tuple[str, ...] = ()
    recipients: tuple[str, ...] = ()
    exit_code: int | None = None
    waiting: bool = False
    successful: bool | None = None

    def key(self) -> tuple[object, ...]:
        return (self.thread, self.turn, self.item, self.request, self.kind, self.phase, self.child)


@dataclass(frozen=True)
class ThreadMetadata:
    thread: str
    cwd: Path
    status: str
    parent: str | None
    native_nickname: str | None
    role: str | None
    waiting: bool

    @classmethod
    def parse(cls, value: dict[str, Any]) -> "ThreadMetadata":
        status = value.get("status")
        if (
            not identifier(value.get("id"))
            or not isinstance(value.get("cwd"), str)
            or not isinstance(status, dict)
            or status.get("type") not in {"active", "idle"}
        ):
            raise NativeUnavailable("Thread is malformed or not already loaded")
        return cls(
            value["id"],
            Path(value["cwd"]),
            status["type"],
            identifier(value.get("parentThreadId")),
            nickname(value.get("agentNickname")),
            nickname(value.get("agentRole")),
            "waitingOnUserInput" in status.get("activeFlags", []),
        )


def parse_event(value: dict[str, Any], workspace: Path) -> Fact | None:
    """Do not retain raw command, prompt, reasoning, diff, output or question content."""
    method = value.get("method")
    params = value.get("params")
    if not isinstance(params, dict) or not (thread := identifier(params.get("threadId"))):
        return None
    turn = identifier(params.get("turnId"))
    if method == "item/tool/requestUserInput":
        request = value.get("id")
        if type(request) not in {str, int}:
            return None
        return Fact("request", thread, turn, identifier(params.get("itemId")), str(request))
    if method == "serverRequest/resolved":
        request = params.get("requestId")
        return (
            Fact("resolved", thread, request=str(request)) if type(request) in {str, int} else None
        )
    if method == "thread/status/changed":
        status = params.get("status")
        if isinstance(status, dict) and status.get("type") in {"active", "idle"}:
            return Fact(
                "status",
                thread,
                phase=status["type"],
                waiting="waitingOnUserInput" in status.get("activeFlags", []),
            )
    if method in {"turn/started", "turn/completed"}:
        data = params.get("turn")
        if isinstance(data, dict) and identifier(data.get("id")):
            phase = data.get("status")
            if phase in {"inProgress", "completed", "failed", "interrupted"}:
                return Fact("turn", thread, data["id"], phase=phase)
    if method not in {"item/started", "item/completed"}:
        return None
    item = params.get("item")
    if not isinstance(item, dict) or not (item_id := identifier(item.get("id"))) or not turn:
        return None
    phase = "start" if method == "item/started" else "finish"
    item_type = item.get("type")
    if item_type == "subAgentActivity":
        child = identifier(item.get("agentThreadId"))
        kind = item.get("kind")
        if child and kind in {"started", "completed"}:
            return Fact("child", thread, turn, item_id, phase=kind, child=child)
    if item_type == "commandExecution":
        command = item.get("command")
        if not isinstance(command, str) or len(command) > 65536:
            return None
        state = state_for_command(command)
        # Safe executable label, never free-form command or arbitrary tool output.
        tool = {AgentState.TESTING: "test", AgentState.SEARCHING: "search"}.get(state, "command")
        code = item.get("exitCode")
        return Fact(
            "command",
            thread,
            turn,
            item_id,
            phase=phase,
            state=state,
            tool=tool,
            exit_code=code if type(code) is int else None,
        )
    if item_type == "fileChange":
        changes = item.get("changes")
        if not isinstance(changes, list):
            return None
        paths = tuple(
            dict.fromkeys(
                path
                for change in changes[:100]
                if isinstance(change, dict) and (path := scoped_path(change.get("path"), workspace))
            )
        )
        return Fact(
            "file",
            thread,
            turn,
            item_id,
            phase=phase,
            paths=paths,
            successful=item.get("status") == "completed" if phase == "finish" else None,
        )
    if item_type == "collabAgentToolCall" and item.get("tool") == "wait":
        recipients = item.get("receiverThreadIds")
        if isinstance(recipients, list) and len(recipients) <= 100:
            return Fact(
                "wait",
                thread,
                turn,
                item_id,
                phase=phase,
                recipients=tuple(x for x in recipients if identifier(x)),
            )
    # Reasoning is deliberately diagnostic-only: absence is not negative evidence.
    return None
