import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import Settings
from backend.observer.codex_usage import CodexUsageMonitor


def test_codex_usage_reports_the_most_constrained_live_window(tmp_path: Path) -> None:
    sessions = tmp_path / "sessions" / "2026" / "09" / "05"
    sessions.mkdir(parents=True)
    reset_at = datetime.now(UTC) + timedelta(hours=2)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "rate_limits": {
                "primary": {
                    "used_percent": 22,
                    "window_minutes": 300,
                    "resets_at": int(reset_at.timestamp()),
                },
                "secondary": {
                    "used_percent": 61,
                    "window_minutes": 10080,
                    "resets_at": int(reset_at.timestamp()),
                },
                "plan_type": "plus",
            },
        },
    }
    (sessions / "rollout.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")

    usage = CodexUsageMonitor(tmp_path / "sessions").snapshot()

    assert usage.status == "available"
    assert usage.remaining_percent == 39
    assert usage.limiting_window == "secondary"
    assert usage.primary is not None
    assert usage.primary.remaining_percent == 78
    assert usage.secondary is not None
    assert usage.secondary.window_minutes == 10080
    assert usage.plan_type == "plus"


def test_codex_usage_endpoint_exposes_the_local_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    sessions = tmp_path / "sessions" / "2026" / "09" / "05"
    sessions.mkdir(parents=True)
    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "type": "event_msg",
        "payload": {
            "type": "token_count",
            "rate_limits": {
                "primary": {
                    "used_percent": 35,
                    "window_minutes": 300,
                    "resets_at": int((datetime.now(UTC) + timedelta(hours=1)).timestamp()),
                }
            },
        },
    }
    (sessions / "rollout.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))

    with TestClient(create_app(Settings.for_project(tmp_path))) as client:
        response = client.get("/api/codex-usage")

    assert response.status_code == 200
    assert response.json()["remaining_percent"] == 65
