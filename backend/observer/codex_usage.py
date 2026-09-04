import json
import os
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.models import CodexUsage, CodexUsageWindow


class CodexUsageMonitor:
    """Read the latest non-expired rate-limit snapshot emitted by Codex."""

    def __init__(self, sessions_path: Path) -> None:
        self.sessions_path = sessions_path

    @classmethod
    def from_environment(cls) -> "CodexUsageMonitor":
        codex_root = Path(os.getenv("CODEX_HOME", Path.home() / ".codex"))
        return cls(codex_root / "sessions")

    def snapshot(self) -> CodexUsage:
        now = datetime.now(UTC)
        for path in self._recent_session_files():
            for line in _reverse_lines(path):
                usage = _parse_usage(line, now)
                if usage is not None:
                    return usage
        return CodexUsage(status="unavailable")

    def _recent_session_files(self) -> list[Path]:
        if not self.sessions_path.is_dir():
            return []
        files: list[tuple[float, Path]] = []
        for path in self.sessions_path.rglob("*.jsonl"):
            try:
                files.append((path.stat().st_mtime, path))
            except OSError:
                continue
        return [path for _, path in sorted(files, reverse=True)[:20]]


def _reverse_lines(path: Path, chunk_size: int = 64 * 1024) -> Iterator[str]:
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            position = stream.tell()
            remainder = b""
            while position > 0:
                read_size = min(chunk_size, position)
                position -= read_size
                stream.seek(position)
                block = stream.read(read_size) + remainder
                lines = block.split(b"\n")
                remainder = lines.pop(0) if position else b""
                for line in reversed(lines):
                    if line:
                        yield line.decode("utf-8")
            if remainder:
                yield remainder.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return


def _parse_usage(line: str, now: datetime) -> CodexUsage | None:
    try:
        event: Any = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(event, Mapping):
        return None
    payload = event.get("payload")
    if not isinstance(payload, Mapping) or payload.get("type") != "token_count":
        return None
    rate_limits = payload.get("rate_limits")
    if not isinstance(rate_limits, Mapping):
        return None

    windows = {
        "primary": _parse_window(rate_limits.get("primary"), now),
        "secondary": _parse_window(rate_limits.get("secondary"), now),
        "individual": _parse_window(rate_limits.get("individual_limit"), now),
    }
    live_windows = {name: window for name, window in windows.items() if window}
    if not live_windows:
        return None
    limiting_name, limiting = min(
        live_windows.items(), key=lambda item: item[1].remaining_percent
    )
    updated_at = _parse_timestamp(event.get("timestamp"))
    plan_type = rate_limits.get("plan_type")
    return CodexUsage(
        status="available",
        remaining_percent=limiting.remaining_percent,
        limiting_window=limiting_name,
        primary=windows["primary"],
        secondary=windows["secondary"],
        individual=windows["individual"],
        plan_type=plan_type if isinstance(plan_type, str) else None,
        updated_at=updated_at,
    )


def _parse_window(value: object, now: datetime) -> CodexUsageWindow | None:
    if not isinstance(value, Mapping):
        return None
    try:
        used_percent = min(100.0, max(0.0, float(value["used_percent"])))
        window_minutes = int(value["window_minutes"])
        resets_at = datetime.fromtimestamp(float(value["resets_at"]), UTC)
    except (KeyError, TypeError, ValueError, OSError, OverflowError):
        return None
    if window_minutes <= 0 or resets_at <= now:
        return None
    return CodexUsageWindow(
        used_percent=used_percent,
        remaining_percent=round(100 - used_percent, 1),
        window_minutes=window_minutes,
        resets_at=resets_at,
    )


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
