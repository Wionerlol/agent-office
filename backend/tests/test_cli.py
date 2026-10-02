import sys
from pathlib import Path

import httpx
import pytest

import backend.cli as cli_module
from backend.cli import build_parser, load_cli_settings, run_wrapped
from backend.config import ServerSettings, Settings
from backend.models import AgentEvent, AgentEventType, EventSource
from backend.runtime.emitters import HttpEventEmitter


def test_office_run_emits_a_real_process_lifecycle(tmp_path: Path) -> None:
    events: list[AgentEvent] = []
    exit_code = run_wrapped(
        [sys.executable, "-c", "print('wrapped agent')"],
        name="Docs Worker",
        provider="custom",
        repository=tmp_path,
        role="Documentation",
        task="Write guide",
        emitter=events.append,
    )

    assert all(event.source is EventSource.WRAPPER for event in events)
    assert exit_code == 0
    assert [event.type for event in events] == [
        AgentEventType.AGENT_STARTED,
        AgentEventType.STATE_CHANGED,
        AgentEventType.STATE_CHANGED,
        AgentEventType.AGENT_STOPPED,
    ]
    assert events[0].payload["agent"]["name"] == "Docs Worker"
    assert events[0].payload["agent"]["pid"] > 0


def test_http_emitter_drops_events_when_office_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable(*args: object, **kwargs: object) -> None:
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "post", unavailable)

    HttpEventEmitter("http://127.0.0.1:8001/api/events")(
        AgentEvent(type=AgentEventType.AGENT_STOPPED, agent_id="agent")
    )


def test_office_run_uses_the_configured_server_from_any_repository() -> None:
    settings = Settings(server=ServerSettings(host="0.0.0.0", port=8001))

    args, _ = build_parser(settings).parse_known_args(["codex"])

    assert args.server == "http://127.0.0.1:8001/api/events"


def test_office_run_loads_agent_office_config_outside_its_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_OFFICE_CONFIG", raising=False)
    expected_path = Path(cli_module.__file__).resolve().parents[1] / "config" / "office.yaml"

    settings = load_cli_settings()

    assert settings.server == Settings.load(expected_path).server
