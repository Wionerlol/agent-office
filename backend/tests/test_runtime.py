from datetime import UTC, datetime

import pytest

from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.runtime.office import OfficeRuntime
from backend.runtime.storage import EventStorage


def make_agent() -> Agent:
    now = datetime.now(UTC)
    return Agent(
        id="backend",
        name="Backend",
        provider="codex",
        pid=123,
        repository="/repo",
        status=AgentState.THINKING,
        task="Build runtime",
        started_at=now,
        last_active_at=now,
    )


@pytest.mark.asyncio
async def test_runtime_projects_events_into_agent_state_and_records_them(tmp_path):
    runtime = OfficeRuntime(storage=EventStorage(tmp_path / "events.jsonl"))
    started = AgentEvent(
        type=AgentEventType.AGENT_STARTED,
        agent_id="backend",
        payload={"agent": make_agent().model_dump(mode="json")},
    )
    changed = AgentEvent(
        type=AgentEventType.STATE_CHANGED,
        agent_id="backend",
        payload={"from": "thinking", "to": "testing"},
    )

    assert (await runtime.apply(started))["type"] == "agent.started"
    update = await runtime.apply(changed)

    assert update == {
        "type": "agent.updated",
        "agent_id": "backend",
        "changes": {"status": "testing"},
    }
    assert runtime.registry.get("backend").status is AgentState.TESTING
    assert [event.type for event in runtime.storage.read()] == [
        AgentEventType.AGENT_STARTED,
        AgentEventType.STATE_CHANGED,
    ]
