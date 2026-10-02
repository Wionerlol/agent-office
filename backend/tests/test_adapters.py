import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.adapters.generic import CustomAgentAdapter, GenericProcessAdapter
from backend.models import AgentEventType, AgentState, EventSource
from backend.observer.process import ProcessSnapshot
from backend.observer.tools import state_for_command, tool_kind


@pytest.mark.asyncio
async def test_generic_adapter_detects_an_explicitly_tagged_process(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": "worker-one",
        "AGENT_OFFICE_NAME": "Worker One",
        "AGENT_OFFICE_PROVIDER": "custom",
        "AGENT_OFFICE_REPOSITORY": str(tmp_path),
        "AGENT_OFFICE_TASK": "Exercise adapter",
    }
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        env=environment,
    )
    try:
        agents = await GenericProcessAdapter(pids=[process.pid]).detect()
    finally:
        process.terminate()
        process.wait(timeout=5)

    stopped = await anext(GenericProcessAdapter().observe(agents[0]))
    assert stopped.source is EventSource.PROCESS
    assert stopped.type is AgentEventType.AGENT_STOPPED
    assert stopped.payload["pid"] == process.pid
    assert len(agents) == 1
    assert agents[0].model_dump(include={"id", "name", "provider", "repository"}) == {
        "id": "worker-one",
        "name": "Worker One",
        "provider": "custom",
        "repository": str(tmp_path),
    }


@pytest.mark.asyncio
async def test_custom_adapter_discovers_a_directly_started_tagged_process(
    tmp_path: Path,
) -> None:
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": "direct-custom",
        "AGENT_OFFICE_PROVIDER": "custom",
        "AGENT_OFFICE_REPOSITORY": str(tmp_path),
    }
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        env=environment,
    )
    try:
        agents = await CustomAgentAdapter().detect()
    finally:
        process.terminate()
        process.wait(timeout=5)

    assert any(agent.id == "direct-custom" for agent in agents)


@pytest.mark.asyncio
async def test_generic_adapter_keeps_a_node_provider_launcher() -> None:
    adapter = GenericProcessAdapter()
    adapter.processes.snapshots = lambda: [
        ProcessSnapshot(
            pid=42,
            parent_pid=1,
            command=["node", "/usr/local/bin/claude"],
            cwd="/repo",
            created_at=0,
            environment={},
        )
    ]

    agents = await adapter.detect()

    assert [(agent.provider, agent.pid) for agent in agents] == [("claude", 42)]


@pytest.mark.parametrize(
    ("command", "state"),
    [
        ("pytest tests/api", AgentState.TESTING),
        ("npm run test", AgentState.TESTING),
        ("rg AgentState backend", AgentState.SEARCHING),
        ("git status", AgentState.TOOL_RUNNING),
    ],
)
def test_commands_are_classified_into_domain_states(command: str, state: AgentState) -> None:
    assert state_for_command(command) is state


@pytest.mark.parametrize(
    ("command", "kind"),
    [
        ("pytest -q", "test"),
        ("rg AgentState", "search"),
        ("git status", "git"),
        ("npm run build", "build"),
        ("ruff check .", "lint"),
        ("bash -lc pwd", "shell"),
        ('bash -lc "rg AgentState backend"', "search"),
        ('bash -lc "npm run build"', "build"),
    ],
)
def test_tool_commands_are_named_for_the_office(command: str, kind: str) -> None:
    assert tool_kind(command) == kind


@pytest.mark.asyncio
async def test_wrapped_descendants_share_identity_and_use_the_root_pid() -> None:
    adapter = GenericProcessAdapter()
    environment = {"AGENT_OFFICE_ID": "backend", "AGENT_OFFICE_PROVIDER": "codex"}
    adapter.processes.snapshots = lambda: [
        ProcessSnapshot(12, 11, ["codex", "exec"], "/repo", 2, environment),
        ProcessSnapshot(11, 1, ["codex"], "/repo", 1, environment),
    ]
    agents = await adapter.detect()
    assert [(agent.id, agent.pid) for agent in agents] == [("backend", 11)]


@pytest.mark.asyncio
async def test_unwrapped_supported_agent_remains_discoverable() -> None:
    adapter = GenericProcessAdapter()
    adapter.processes.snapshots = lambda: [
        ProcessSnapshot(11, 1, ["codex"], "/repo", 1, {}),
    ]
    agents = await adapter.detect()
    assert [(agent.id, agent.pid) for agent in agents] == [("codex-11", 11)]
