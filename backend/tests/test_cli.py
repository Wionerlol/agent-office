import sys
from pathlib import Path

from backend.cli import run_wrapped
from backend.models import AgentEventType
from backend.runtime.emitters import JsonlEventEmitter
from backend.runtime.storage import EventStorage


def test_office_run_records_a_real_process_lifecycle(tmp_path: Path) -> None:
    event_path = tmp_path / "events.jsonl"
    exit_code = run_wrapped(
        [sys.executable, "-c", "print('wrapped agent')"],
        name="Docs Worker",
        provider="custom",
        repository=tmp_path,
        role="Documentation",
        task="Write guide",
        emitter=JsonlEventEmitter(EventStorage(event_path)),
    )

    events = EventStorage(event_path).read()
    assert exit_code == 0
    assert [event.type for event in events] == [
        AgentEventType.AGENT_STARTED,
        AgentEventType.STATE_CHANGED,
        AgentEventType.STATE_CHANGED,
        AgentEventType.AGENT_STOPPED,
    ]
    assert events[0].payload["agent"]["name"] == "Docs Worker"
    assert events[0].payload["agent"]["pid"] > 0
