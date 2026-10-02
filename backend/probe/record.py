"""Project native records through a content-denying diagnostic schema."""

import hashlib
import json
import math
import os
import re
import shlex
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

# Unknown fields are discarded, not recursively copied. Free text is never retained.
CONTAINERS = frozenset(
    {
        "item",
        "thread",
        "turn",
        "status",
        "payload",
        "msg",
        "source",
        "sub_agent",
        "thread_spawn",
        "subAgent",
        "changes",
        "actions",
        "plan",
        "questions",
        "options",
        "answers",
        "agentsStates",
        "agents_states",
        "result",
        "error",
        "usage",
        "commandActions",
    }
)
IDENTIFIERS = frozenset(
    {
        "id",
        "threadId",
        "thread_id",
        "sessionId",
        "session_id",
        "turnId",
        "turn_id",
        "itemId",
        "item_id",
        "call_id",
        "parentThreadId",
        "parent_thread_id",
        "senderThreadId",
        "receiverThreadId",
        "receiverThreadIds",
        "receiver_thread_ids",
        "sender_thread_id",
        "agentThreadId",
        "agent_id",
        "parent_agent_id",
        "processId",
        "requestId",
    }
)
ENUMS = frozenset(
    {
        "type",
        "status",
        "tool",
        "name",
        "agentRole",
        "agentNickname",
        "agent_role",
        "agent_nickname",
        "role",
        "kind",
        "phase",
        "mode",
        "cliVersion",
        "originator",
        "activeFlags",
        "reason",
        "method",
    }
)
NUMBERS = frozenset(
    {
        "exitCode",
        "exit_code",
        "durationMs",
        "duration_ms",
        "pid",
        "createdAt",
        "updatedAt",
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "depth",
        "code",
        "canAcceptDirectInput",
        "isOther",
        "isSecret",
    }
)
TEXT = frozenset(
    {
        "text",
        "delta",
        "summary",
        "content",
        "message",
        "prompt",
        "question",
        "header",
        "label",
        "description",
        "arguments",
        "output",
        "aggregatedOutput",
        "diff",
        "patch",
        "unified_diff",
        "instructions",
        "preview",
        "task",
        "answer",
        "encrypted_content",
    }
)
SAFE_WORD = re.compile(r"[A-Za-z0-9_. /:-]{1,100}\Z")
SECRET = re.compile(r"(?i)(sk-|gh[pousr]_|bearer|password|secret|token=|eyJ)")
TOOLS = frozenset(
    {
        "apply_patch",
        "exec_command",
        "spawn_agent",
        "wait",
        "close_agent",
        "request_user_input",
        "write_stdin",
        "send_input",
        "send_message",
        "functions.apply_patch",
        "functions.exec_command",
        "functions.spawn_agent",
        "functions.request_user_input",
        "functions.wait",
        "functions.write_stdin",
        "functions.close_agent",
    }
)
EXECUTABLES = frozenset(
    {
        "rg",
        "grep",
        "cat",
        "sed",
        "ls",
        "pwd",
        "echo",
        "printf",
        "sleep",
        "true",
        "python",
        "python3",
        "pytest",
        "uv",
        "bash",
        "sh",
        "git",
        "npm",
        "node",
    }
)


def opaque_id(value: object) -> str | None:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return None
    return "id-" + hashlib.sha256(str(value).encode()).hexdigest()[:20]


def safe_word(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, list):
        return [safe_word(item) for item in value[:100]]
    if isinstance(value, str) and SAFE_WORD.fullmatch(value) and not SECRET.search(value):
        return value
    return "[redacted]"


def command_facts(value: object) -> dict[str, object]:
    """Record executable tokens, never arguments, shell bodies or output."""
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        tokens = value
    elif isinstance(value, str):
        try:
            tokens = shlex.split(value)
        except ValueError:
            tokens = []
    else:
        tokens = []
    # A token match is a diagnostic executable hint, not a domain-state classifier.
    executables = sorted({Path(token).name for token in tokens if Path(token).name in EXECUTABLES})
    return {"redacted": True, "executable_tokens": executables}


class Projector:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    def path(self, value: object) -> str:
        if not isinstance(value, str):
            return "[redacted]"
        candidate = Path(value)
        candidate = candidate if candidate.is_absolute() else self.workspace / candidate
        try:
            relative = candidate.resolve().relative_to(self.workspace)
        except (ValueError, OSError):
            return "[outside-workspace]"
        text = relative.as_posix()
        return text if not SECRET.search(text) and len(text) <= 200 else "[redacted]"

    def project(self, value: object, depth: int = 0) -> Any:
        if depth > 12:
            return "[depth-limit]"
        if isinstance(value, list):
            return [self.project(item, depth + 1) for item in value[:100]]
        if not isinstance(value, dict):
            return None
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key in IDENTIFIERS:
                result[key] = (
                    [opaque_id(identifier) for identifier in item[:100]]
                    if isinstance(item, list)
                    else opaque_id(item)
                )
            elif key in {"subAgent", "source"} and isinstance(item, str):
                result[key] = safe_word(item)
            elif key in {"status", "kind", "source"} and isinstance(item, dict):
                result[key] = self.project(item, depth + 1)
            elif key == "source" and isinstance(item, str):
                result[key] = safe_word(item)
            elif key in ENUMS:
                # Thread titles and arbitrary tool/message names are user content.
                result[key] = (
                    item
                    if key == "name" and isinstance(item, str) and item in TOOLS
                    else "[redacted]"
                    if key == "name"
                    else safe_word(item)
                )
            elif (
                key in NUMBERS
                and isinstance(item, (int, float, bool))
                and (not isinstance(item, float) or math.isfinite(item))
            ):
                result[key] = item
            elif key in TEXT:
                result[key] = (
                    item
                    if item is None or (isinstance(item, (str, list, dict)) and not item)
                    else "[redacted]"
                )
            elif key in {"command", "cmd", "argv"}:
                result[key] = command_facts(item)
            elif key in {"path", "file_path", "cwd"}:
                result[key] = self.path(item)
            elif key in {"agentsStates", "agents_states"} and isinstance(item, dict):
                result[key] = {
                    str(opaque_id(identifier)): self.project(state, depth + 1)
                    for identifier, state in list(item.items())[:100]
                }
            elif key == "changes" and isinstance(item, dict):
                # Rollout patch maps use paths as keys; app-server uses a list instead.
                result[key] = [
                    {"path": self.path(path), "change": self.project(change, depth + 1)}
                    for path, change in list(item.items())[:100]
                ]
            elif key in CONTAINERS:
                result[key] = self.project(item, depth + 1)
        return result


class ProbeRecorder:
    def __init__(self, output: TextIO, source: str, workspace: Path) -> None:
        self.output = output
        self.source = source
        self.projector = Projector(workspace)
        self.sequence = 0
        self.session_id: str | None = None

    def record(self, value: object) -> dict[str, Any]:
        self.sequence += 1
        received = datetime.now(UTC).isoformat()
        if not isinstance(value, dict):
            value = {"type": "probe.malformed"}
        raw_type = value.get("method", value.get("type", "probe.response"))
        if not isinstance(raw_type, str):
            value = {"type": "probe.malformed"}
            raw_type = "probe.malformed"
        body = value.get("params", value)
        body = body if isinstance(body, dict) else {}
        thread = body.get("thread", {})
        thread = thread if isinstance(thread, dict) else {}
        identifier = body.get("threadId") or body.get("thread_id") or thread.get("id")
        if raw_type == "session_meta":
            payload = body.get("payload")
            identifier = payload.get("id") if isinstance(payload, dict) else None
        if identifier:
            session = opaque_id(identifier)
            if self.source == "codex-exec" or raw_type == "session_meta":
                self.session_id = session
        else:
            session = self.session_id
        provider_timestamp = None
        timestamp = value.get("timestamp")
        if isinstance(timestamp, str):
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                provider_timestamp = timestamp
            except ValueError:
                pass
        record = {
            "sequence": self.sequence,
            "timestamp": received,
            "provider_timestamp": provider_timestamp,
            "provider_sequence": value.get("ordinal")
            if type(value.get("ordinal")) is int
            else None,
            "provider": "codex",
            "session_id": session,
            "raw_type": safe_word(raw_type),
            "request_id": opaque_id(value.get("id")) if "method" in value else None,
            "source": self.source,
            "payload": self.projector.project(body),
        }
        self.output.write(json.dumps(record, ensure_ascii=True, allow_nan=False) + "\n")
        self.output.flush()
        return record

    def line(self, line: str) -> dict[str, Any]:
        try:
            value = json.loads(line) if len(line) <= 1_048_576 else None
        except (ValueError, RecursionError):
            value = None
        return self.record(value)


def private_output(path: Path) -> TextIO:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    return os.fdopen(descriptor, "w", encoding="utf-8")
