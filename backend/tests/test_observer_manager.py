import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.adapters.generic import GenericProcessAdapter
from backend.config import ObserverSettings
from backend.models import EventSource
from backend.observer.manager import ObserverManager
from backend.runtime.office import OfficeRuntime


@pytest.mark.asyncio
async def test_manager_tracks_detected_process_until_it_exits(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": "managed-worker",
        "AGENT_OFFICE_NAME": "Managed Worker",
        "AGENT_OFFICE_PROVIDER": "custom",
        "AGENT_OFFICE_REPOSITORY": str(tmp_path),
    }
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        env=environment,
    )
    runtime = OfficeRuntime()
    manager = ObserverManager(
        runtime,
        ObserverSettings(enabled=True, scan_interval=0.01),
        adapters=[GenericProcessAdapter(pids=[process.pid])],
    )
    try:
        await manager.run_once()
        assert runtime.registry.get("managed-worker").pid == process.pid
        assert runtime.status_evidence("managed-worker").source is EventSource.PROCESS

        process.terminate()
        process.wait(timeout=5)
        await manager.run_once()
        with pytest.raises(KeyError):
            runtime.registry.get("managed-worker")
    finally:
        if process.poll() is None:
            process.terminate()


@pytest.mark.asyncio
async def test_timeout_source_and_wrapper_discovery_race() -> None:
    from datetime import UTC, datetime, timedelta

    from backend.models import Agent, AgentEvent, AgentEventType, AgentState

    runtime = OfficeRuntime()
    adapter = GenericProcessAdapter(pids=[])
    manager = ObserverManager(runtime, ObserverSettings(idle_timeout=0), adapters=[adapter])
    await manager.run_once()
    now = datetime.now(UTC) - timedelta(seconds=1)
    agent = Agent(
        id="wrapped", name="Wrapped", provider="codex", repository="/repo", last_active_at=now
    )
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            agent_id=agent.id,
            timestamp=now,
            source=EventSource.WRAPPER,
            payload={"agent": agent.model_dump(mode="json")},
        )
    )
    passive = agent.model_copy(update={"name": "Passive"})

    async def detect() -> list[Agent]:
        return [passive]

    adapter.detect = detect
    try:
        await manager.run_once()
        assert runtime.registry.get(agent.id).name == "Wrapped"
        assert runtime.registry.get(agent.id).status is AgentState.IDLE
        assert runtime.status_evidence(agent.id).source is EventSource.TIMEOUT
        await runtime.apply(
            AgentEvent(
                type=AgentEventType.TOOL_STARTED,
                agent_id=agent.id,
                source=EventSource.TOOL_PROCESS,
                payload={"command": "pytest"},
            )
        )
        await manager._mark_idle(agent.id)
        assert runtime.registry.get(agent.id).status is AgentState.TESTING
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_detection_failure_does_not_stop_a_registered_agent() -> None:
    from backend.models import Agent
    from backend.state.registry import AgentRegistry

    agent = Agent(
        id="wrapped", name="Wrapped", provider="codex", pid=os.getpid(), repository="/repo"
    )
    runtime = OfficeRuntime(registry=AgentRegistry([agent]))
    adapter = GenericProcessAdapter(pids=[])

    async def fail() -> list[Agent]:
        raise PermissionError("process enumeration unavailable")

    adapter.detect = fail
    manager = ObserverManager(runtime, ObserverSettings(), adapters=[adapter])
    await manager.run_once()
    assert runtime.registry.get(agent.id).pid == os.getpid()

    async def empty() -> list[Agent]:
        return []

    adapter.detect = empty
    await manager.run_once()
    assert runtime.registry.get(agent.id).pid == os.getpid()
    await manager.stop()
