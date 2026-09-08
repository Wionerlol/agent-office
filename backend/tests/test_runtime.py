from datetime import UTC, datetime

import pytest

from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.runtime.office import OfficeRuntime
from backend.state.engine import StateTransitionError


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
async def test_runtime_projects_events_into_live_agent_state() -> None:
    runtime = OfficeRuntime()
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


@pytest.mark.asyncio
async def test_runtime_rejects_a_stale_state_transition() -> None:
    runtime = OfficeRuntime()
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            agent_id="backend",
            payload={"agent": make_agent().model_dump(mode="json")},
        )
    )

    with pytest.raises(StateTransitionError, match="Stale transition"):
        await runtime.apply(
            AgentEvent(
                type=AgentEventType.STATE_CHANGED,
                agent_id="backend",
                payload={"from": "coding", "to": "testing"},
            )
        )
