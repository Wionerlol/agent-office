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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_OFFICE_CONFIG", raising=False)
    expected_path = Path(cli_module.__file__).resolve().parents[1] / "config" / "office.yaml"

    settings = load_cli_settings()

    assert settings.server == Settings.load(expected_path).server


def test_office_run_propagates_semantics_to_the_process_and_registration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    monkeypatch.setenv("AGENT_OFFICE_ROLE", "research")
    monkeypatch.setenv("AGENT_OFFICE_PARENT_ID", "other-parent")
    monkeypatch.setenv("AGENT_OFFICE_DEFINITION_ID", "researcher")
    monkeypatch.setenv("AGENT_OFFICE_RESPONSIBILITIES", '["Research options"]')
    events: list[AgentEvent] = []
    output = tmp_path / "environment.json"
    command = [
        sys.executable,
        "-c",
        "import os,json; from pathlib import Path; "
        "Path('environment.json').write_text(json.dumps({k:v for k,v in os.environ.items() "
        "if k.startswith('AGENT_OFFICE_')}))",
    ]
    code = run_wrapped(
        command,
        name="Worker",
        provider="custom",
        repository=tmp_path,
        role="backend",
        task="Verify auth",
        parent_agent_id="lead",
        definition_id="tester",
        responsibilities=["Run tests"],
        emitter=events.append,
    )
    assert code == 0
    identity = events[0].payload["agent"]
    environment = json.loads(output.read_text())
    assert identity["parent_agent_id"] == environment["AGENT_OFFICE_PARENT_ID"] == "lead"
    assert identity["definition_id"] == environment["AGENT_OFFICE_DEFINITION_ID"] == "tester"
    assert identity["role"] == environment["AGENT_OFFICE_ROLE"] == "backend"
    assert (
        identity["responsibilities"]
        == json.loads(environment["AGENT_OFFICE_RESPONSIBILITIES"])
        == ["Run tests"]
    )
    assert identity["id"] == environment["AGENT_OFFICE_ID"]
    assert identity["id"].startswith("tester-")
    assert identity["task"] == "Verify auth"


def test_semantic_cli_flags_leave_provider_options_intact() -> None:
    args, rest = build_parser().parse_known_args(
        [
            "codex",
            "--parent",
            "lead",
            "--definition",
            "tester",
            "--role",
            "backend",
            "--responsibility",
            "Unit tests",
            "--responsibility",
            "Integration tests",
            "exec",
            "--sandbox",
            "read-only",
            "--parent-option",
            "provider-value",
        ]
    )
    assert args.parent_agent_id == "lead"
    assert args.definition_id == "tester"
    assert args.role == "backend"
    assert args.responsibilities == ["Unit tests", "Integration tests"]
    assert rest == ["exec", "--sandbox", "read-only", "--parent-option", "provider-value"]


def test_definition_instances_get_distinct_ids_and_use_environment_defaults(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_OFFICE_DEFINITION_ID", "tester")
    monkeypatch.setenv("AGENT_OFFICE_PARENT_ID", "lead")
    monkeypatch.setenv("AGENT_OFFICE_ROLE", "tester")
    monkeypatch.setenv("AGENT_OFFICE_RESPONSIBILITIES", '["Run unit tests"]')
    events: list[AgentEvent] = []
    for _ in range(2):
        assert (
            run_wrapped(
                [sys.executable, "-c", "pass"],
                name="Codex",
                provider="custom",
                repository=tmp_path,
                role=None,
                task=None,
                emitter=events.append,
            )
            == 0
        )
    started = [
        event.payload["agent"] for event in events if event.type is AgentEventType.AGENT_STARTED
    ]
    assert started[0]["id"] != started[1]["id"]
    assert all(agent["parent_agent_id"] == "lead" for agent in started)
    assert all(agent["responsibilities"] == ["Run unit tests"] for agent in started)


def test_main_passes_semantic_flags_to_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, object] = {}

    def run(command: object, **arguments: object) -> int:
        received.update(arguments)
        return 0

    monkeypatch.setattr(cli_module, "run_wrapped", run)
    with pytest.raises(SystemExit) as exit_info:
        cli_module.main(
            ["codex", "--parent", "lead", "--definition", "tester", "--responsibility", "Run tests"]
        )
    assert exit_info.value.code == 0
    assert received["parent_agent_id"] == "lead"
    assert received["definition_id"] == "tester"
    assert received["responsibilities"] == ["Run tests"]
