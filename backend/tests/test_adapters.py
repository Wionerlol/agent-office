import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.adapters.generic import GenericProcessAdapter
from backend.models import AgentState
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

    assert len(agents) == 1
    assert agents[0].model_dump(include={"id", "name", "provider", "repository"}) == {
        "id": "worker-one",
        "name": "Worker One",
        "provider": "custom",
        "repository": str(tmp_path),
    }


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
