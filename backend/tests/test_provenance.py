from datetime import UTC, datetime, timedelta

import pytest

from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.runtime.office import OfficeRuntime
from backend.state.provenance import SOURCE_PRIORITY

NOW = datetime(2026, 1, 1, tzinfo=UTC)


async def started_runtime(source: EventSource = EventSource.WRAPPER) -> OfficeRuntime:
    runtime = OfficeRuntime()
    agent = Agent(
        id="worker",
        name="Worker",
        provider="codex",
        repository="/repo",
        started_at=NOW,
        last_active_at=NOW,
    )
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            agent_id=agent.id,
            timestamp=NOW,
            source=source,
            payload={"agent": agent.model_dump(mode="json")},
        )
    )
    return runtime


def event(kind: AgentEventType, source: EventSource, seconds: int, **payload: object) -> AgentEvent:
    return AgentEvent(
        type=kind,
        agent_id="worker",
        source=source,
        timestamp=NOW + timedelta(seconds=seconds),
        payload=payload,
    )


def test_legacy_event_and_naive_timestamp_are_compatible() -> None:
    parsed = AgentEvent.model_validate(
        {
            "type": "agent.state_changed",
            "agent_id": "worker",
            "timestamp": "2026-01-01T00:00:00",
            "payload": {"to": "coding"},
        }
    )
    assert parsed.source is EventSource.API
    assert parsed.timestamp == NOW


def test_priority_order_is_explicit_including_api() -> None:
    ordered = [
        EventSource.NATIVE,
        EventSource.WRAPPER,
        EventSource.API,
        EventSource.TOOL_PROCESS,
        EventSource.FILESYSTEM,
        EventSource.GIT,
        EventSource.PROCESS,
        EventSource.TIMEOUT,
    ]
    assert set(SOURCE_PRIORITY) == set(EventSource)
    assert all(
        SOURCE_PRIORITY[a] > SOURCE_PRIORITY[b] for a, b in zip(ordered, ordered[1:], strict=False)
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source", [EventSource.FILESYSTEM, EventSource.GIT, EventSource.PROCESS, EventSource.TIMEOUT]
)
@pytest.mark.parametrize("seconds", [0, 2, 20])
@pytest.mark.parametrize("command", ["pytest", "rg symbol", "sleep 10"])
async def test_weaker_evidence_does_not_change_testing_or_activity_clock(
    source: EventSource,
    seconds: int,
    command: str,
) -> None:
    runtime = await started_runtime()
    await runtime.apply(
        event(
            AgentEventType.TOOL_STARTED, EventSource.TOOL_PROCESS, 1, tool="test", command=command
        )
    )
    before = runtime.registry.get("worker").model_copy(deep=True)
    queue = runtime.bus.subscribe()
    result = await runtime.apply(event(AgentEventType.STATE_CHANGED, source, seconds, to="idle"))
    assert result["changes"] == {}
    assert runtime.registry.get("worker") == before
    assert queue.empty()
    assert runtime.status_evidence("worker").source is EventSource.TOOL_PROCESS


@pytest.mark.asyncio
async def test_recency_and_equal_authority_and_stronger_sources() -> None:
    runtime = await started_runtime()
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.WRAPPER, 10, to="coding"))
    for source in [EventSource.WRAPPER, EventSource.NATIVE]:
        assert (await runtime.apply(event(AgentEventType.STATE_CHANGED, source, 5, to="waiting")))[
            "changes"
        ] == {}
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.WRAPPER, 15, to="done"))
    assert runtime.registry.get("worker").status is AgentState.DONE
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.NATIVE, 20, to="waiting"))
    assert runtime.registry.get("worker").status is AgentState.WAITING
    assert runtime.status_evidence("worker").observed_at == NOW + timedelta(seconds=20)


@pytest.mark.asyncio
async def test_wrapper_baseline_allows_tools_and_finished_tools_allow_idle() -> None:
    runtime = await started_runtime()
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.WRAPPER, 1, to="thinking"))
    await runtime.apply(
        event(
            AgentEventType.TOOL_STARTED,
            EventSource.TOOL_PROCESS,
            2,
            tool="search",
            command="rg symbol",
        )
    )
    assert runtime.registry.get("worker").status is AgentState.SEARCHING
    await runtime.apply(event(AgentEventType.TOOL_FINISHED, EventSource.TOOL_PROCESS, 3))
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.TIMEOUT, 40, to="idle"))
    assert runtime.registry.get("worker").status is AgentState.IDLE


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["waiting", "done", "error", "offline"])
async def test_tools_cannot_revive_authoritative_terminal_or_waiting_states(status: str) -> None:
    runtime = await started_runtime()
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.WRAPPER, 1, to=status))
    await runtime.apply(
        event(AgentEventType.TOOL_STARTED, EventSource.TOOL_PROCESS, 2, command="pytest")
    )
    await runtime.apply(event(AgentEventType.TOOL_FINISHED, EventSource.TOOL_PROCESS, 3))
    assert runtime.registry.get("worker").status.value == status
    assert runtime.registry.get("worker").current_tool is None


@pytest.mark.asyncio
async def test_duplicate_discovery_preserves_wrapper_identity_and_activity() -> None:
    runtime = await started_runtime()
    await runtime.apply(
        event(AgentEventType.TOOL_STARTED, EventSource.TOOL_PROCESS, 1, command="pytest")
    )
    duplicate = Agent(id="worker", name="Passive", provider="codex", repository="/other")
    await runtime.apply(
        event(
            AgentEventType.AGENT_STARTED,
            EventSource.PROCESS,
            2,
            agent=duplicate.model_dump(mode="json"),
        )
    )
    assert len(runtime.registry.all()) == 1
    assert runtime.registry.get("worker").name == "Worker"
    assert runtime.registry.get("worker").status is AgentState.TESTING


@pytest.mark.asyncio
async def test_wrapper_enriches_passive_identity_without_resetting_activity() -> None:
    runtime = await started_runtime(EventSource.PROCESS)
    await runtime.apply(
        event(AgentEventType.TOOL_STARTED, EventSource.TOOL_PROCESS, 1, command="pytest")
    )
    wrapped = Agent(
        id="worker", name="Wrapped", provider="codex", repository="/repo", role="Backend"
    )
    result = await runtime.apply(
        event(
            AgentEventType.AGENT_STARTED,
            EventSource.WRAPPER,
            2,
            agent=wrapped.model_dump(mode="json"),
        )
    )
    assert result["type"] == "agent.updated"
    assert runtime.registry.get("worker").role == "Backend"
    assert runtime.registry.get("worker").status is AgentState.TESTING


@pytest.mark.asyncio
async def test_lifecycle_stop_overrides_activity_but_not_newer_timestamps() -> None:
    runtime = await started_runtime()
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.NATIVE, 10, to="testing"))
    for source, seconds in [(EventSource.PROCESS, 5), (EventSource.TIMEOUT, 20)]:
        await runtime.apply(event(AgentEventType.AGENT_STOPPED, source, seconds))
        assert len(runtime.registry.all()) == 1
    await runtime.apply(event(AgentEventType.AGENT_STOPPED, EventSource.PROCESS, 20))
    assert runtime.registry.all() == []
    assert (await runtime.apply(event(AgentEventType.AGENT_STOPPED, EventSource.WRAPPER, 21)))[
        "type"
    ] == "agent.stopped"


@pytest.mark.asyncio
async def test_error_is_arbitrated_and_stale_nonstatus_events_do_not_rewind_clock() -> None:
    runtime = await started_runtime()
    await runtime.apply(event(AgentEventType.STATE_CHANGED, EventSource.NATIVE, 10, to="coding"))
    await runtime.apply(event(AgentEventType.ERROR, EventSource.PROCESS, 20, message="untrusted"))
    assert "last_error" not in runtime.registry.get("worker").metadata
    await runtime.apply(event(AgentEventType.FILE_CHANGED, EventSource.FILESYSTEM, 5, file="a.py"))
    assert runtime.registry.get("worker").last_active_at == NOW + timedelta(seconds=10)
    await runtime.apply(event(AgentEventType.ERROR, EventSource.NATIVE, 15, message="failure"))
    assert runtime.registry.get("worker").status is AgentState.ERROR
    assert runtime.registry.get("worker").metadata["last_error"] == "failure"


@pytest.mark.asyncio
async def test_stop_for_an_old_pid_does_not_remove_current_identity() -> None:
    runtime = await started_runtime()
    runtime.registry.update("worker", pid=20)
    result = await runtime.apply(
        event(AgentEventType.AGENT_STOPPED, EventSource.PROCESS, 10, pid=10)
    )
    assert result["changes"] == {}
    assert runtime.registry.get("worker").pid == 20


@pytest.mark.asyncio
async def test_authoritative_completion_clears_tool_in_backend_and_websocket_update() -> None:
    runtime = await started_runtime()
    await runtime.apply(
        event(
            AgentEventType.TOOL_STARTED, EventSource.TOOL_PROCESS, 1, tool="test", command="pytest"
        )
    )
    result = await runtime.apply(
        event(AgentEventType.STATE_CHANGED, EventSource.WRAPPER, 2, to="done")
    )
    assert result["changes"] == {"status": "done", "current_tool": None}
    assert runtime.registry.get("worker").current_tool is None
    await runtime.apply(event(AgentEventType.TOOL_FINISHED, EventSource.TOOL_PROCESS, 3))
    assert runtime.registry.get("worker").status is AgentState.DONE
