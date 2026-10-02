from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.config import ProjectSettings, Settings
from backend.models import (
    Agent,
    AgentDefinition,
    AgentEvent,
    AgentEventType,
    AgentState,
    EventSource,
)
from backend.runtime.office import OfficeRuntime
from backend.state.identity import AgentDefinitionRegistry

NOW = datetime(2026, 10, 2, tzinfo=UTC)
TESTER = AgentDefinition(
    id="tester",
    name="Tester",
    role="tester",
    responsibilities=["Run unit tests", "Investigate failures"],
)


def settings_for(repository: str = "/repo") -> Settings:
    return Settings(project=ProjectSettings(path=Path(repository)), agents=[TESTER])


def make_agent(**changes: object) -> Agent:
    return Agent.model_validate(
        {
            "id": "child-1",
            "name": "Codex 42",
            "provider": "codex",
            "repository": "/repo",
            "started_at": NOW,
            "last_active_at": NOW,
            **changes,
        }
    )


def start(agent: Agent, source: EventSource = EventSource.WRAPPER, seconds: int = 0) -> AgentEvent:
    return AgentEvent(
        type=AgentEventType.AGENT_STARTED,
        agent_id=agent.id,
        source=source,
        timestamp=NOW + timedelta(seconds=seconds),
        payload={"agent": agent.model_dump(mode="json")},
    )


def test_legacy_agents_and_definition_defaults_are_safe() -> None:
    legacy = make_agent()
    assert legacy.role is None
    assert legacy.responsibilities == []
    assert legacy.parent_agent_id is None
    assert legacy.definition_id is None
    legacy.responsibilities.append("One assignment")
    assert make_agent().responsibilities == []
    assert AgentDefinition(id="reviewer", name="Reviewer").responsibilities == []


def test_project_yaml_loads_root_and_per_project_definitions(tmp_path: Path) -> None:
    config = tmp_path / "config" / "office.yaml"
    config.parent.mkdir()
    config.write_text(
        """project:
  name: demo
  path: .
agents:
  - id: tester
    name: Tester
    role: tester
    responsibilities: [Run unit tests, Investigate failures]
projects:
  - name: another
    path: ../another
    agents:
      - id: tester
        name: Other Tester
        role: qa
""",
        encoding="utf-8",
    )
    settings = Settings.load(config)
    registry = AgentDefinitionRegistry(settings)
    assert settings.agents == [TESTER]
    assert registry.match(make_agent(repository=str(tmp_path), definition_id="tester")) == TESTER
    other = registry.match(
        make_agent(repository=str(tmp_path.parent / "another"), definition_id="tester")
    )
    assert other is not None and other.name == "Other Tester"
    assert registry.match(make_agent(repository="/unconfigured", definition_id="tester")) is None


def test_duplicate_definition_ids_fail_clearly() -> None:
    with pytest.raises(ValidationError, match="unique"):
        Settings(agents=[TESTER, TESTER])
    settings = settings_for()
    settings.projects = [ProjectSettings(path=Path("/repo"), agents=[TESTER])]
    with pytest.raises(ValueError, match="Duplicate agent definition"):
        AgentDefinitionRegistry(settings)


@pytest.mark.asyncio
@pytest.mark.parametrize("source", [EventSource.WRAPPER, EventSource.API, EventSource.PROCESS])
async def test_definition_enriches_runtime_subagent_without_changing_runtime_facts(
    source: EventSource,
) -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    agent = make_agent(
        definition_id="tester",
        parent_agent_id="lead",
        status="testing",
        task="Verify authentication changes",
        current_tool="pytest",
        role="temporary",
    )
    message = await runtime.apply(start(agent, source))
    actual = runtime.registry.get(agent.id)
    assert actual.name == "Tester"
    assert actual.role == "tester"
    assert actual.responsibilities == TESTER.responsibilities
    assert actual.parent_agent_id == "lead"
    assert actual.definition_id == "tester"
    assert actual.task == "Verify authentication changes"
    assert actual.status is AgentState.TESTING
    assert actual.current_tool == "pytest"
    assert runtime.status_evidence(agent.id).source is source
    assert message["type"] == "agent.started"
    assert message["agent"]["name"] == "Tester"


@pytest.mark.asyncio
async def test_definition_can_match_instance_id_and_worktree() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    agent = make_agent(id="tester", repository="/worktrees/run", worktree="/repo")
    await runtime.apply(start(agent))
    assert runtime.registry.get("tester").definition_id == "tester"
    assert runtime.registry.get("tester").name == "Tester"


@pytest.mark.asyncio
async def test_native_metadata_overrides_definition_field_by_field() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    agent = make_agent(
        definition_id="tester",
        name="Security Tester",
        role="security",
        parent_agent_id="native-lead",
        responsibilities=["Audit authentication"],
    )
    await runtime.apply(start(agent, EventSource.NATIVE))
    actual = runtime.registry.get(agent.id)
    assert actual.name == "Security Tester"
    assert actual.role == "security"
    assert actual.responsibilities == ["Audit authentication"]
    assert actual.parent_agent_id == "native-lead"
    # A native registration with omitted role/responsibilities can still use definition defaults.
    other = make_agent(id="child-2", definition_id="tester", name="Native Worker")
    await runtime.apply(start(other, EventSource.NATIVE))
    assert runtime.registry.get(other.id).name == "Native Worker"
    assert runtime.registry.get(other.id).role == "tester"


@pytest.mark.asyncio
async def test_passive_or_incomplete_registration_preserves_semantics_and_current_activity() -> (
    None
):
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    agent = make_agent(definition_id="tester", parent_agent_id="lead")
    await runtime.apply(start(agent))
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            agent_id=agent.id,
            source=EventSource.TOOL_PROCESS,
            timestamp=NOW + timedelta(seconds=1),
            payload={"command": "pytest", "tool": "test"},
        )
    )
    evidence = runtime.status_evidence(agent.id)
    await runtime.apply(start(make_agent(), EventSource.PROCESS, 2))
    await runtime.apply(start(make_agent(), EventSource.WRAPPER, 3))
    actual = runtime.registry.get(agent.id)
    assert actual.name == "Tester"
    assert actual.parent_agent_id == "lead"
    assert actual.definition_id == "tester"
    assert actual.responsibilities == TESTER.responsibilities
    assert actual.status is AgentState.TESTING
    assert actual.current_tool == "test"
    assert runtime.status_evidence(agent.id) == evidence


@pytest.mark.asyncio
async def test_native_enrichment_of_existing_agent_is_broadcast_without_resetting_state() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    agent = make_agent(definition_id="tester", status="testing", parent_agent_id="lead")
    await runtime.apply(start(agent))
    queue = runtime.bus.subscribe()
    native = agent.model_copy(
        update={"name": "QA Lead", "role": "quality", "parent_agent_id": "orchestrator"}
    )
    update = await runtime.apply(start(native, EventSource.NATIVE, 2))
    assert await queue.get() == update
    assert update["type"] == "agent.updated"
    assert update["changes"]["name"] == "QA Lead"
    assert update["changes"]["parent_agent_id"] == "orchestrator"
    assert "status" not in update["changes"]
    assert runtime.registry.get(agent.id).status is AgentState.TESTING
    await runtime.apply(start(agent, EventSource.NATIVE, 1))
    assert runtime.registry.get(agent.id).name == "QA Lead"


@pytest.mark.asyncio
async def test_roles_never_follow_current_tool_and_unregistered_agents_keep_fallback_identity() -> (
    None
):
    runtime = OfficeRuntime()
    agent = make_agent(name="Backend Engineer", role="backend", parent_agent_id="external-parent")
    await runtime.apply(start(agent))
    for seconds, command, state in [
        (1, "pytest", AgentState.TESTING),
        (2, "rg symbol", AgentState.SEARCHING),
    ]:
        await runtime.apply(
            AgentEvent(
                type=AgentEventType.TOOL_STARTED,
                agent_id=agent.id,
                timestamp=NOW + timedelta(seconds=seconds),
                source=EventSource.TOOL_PROCESS,
                payload={"command": command},
            )
        )
        assert runtime.registry.get(agent.id).role == "backend"
        assert runtime.registry.get(agent.id).status is state
    assert runtime.registry.get(agent.id).parent_agent_id == "external-parent"
    assert runtime.registry.get(agent.id).name == "Backend Engineer"


@pytest.mark.asyncio
async def test_unknown_definition_is_fallback_and_multiple_instances_remain_distinct() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    for identifier in ["child-1", "child-2"]:
        await runtime.apply(start(make_agent(id=identifier, definition_id="tester")))
    assert [agent.name for agent in runtime.registry.all()] == ["Tester", "Tester"]
    await runtime.apply(start(make_agent(id="tester", definition_id="missing")))
    assert runtime.registry.get("tester").name == "Codex 42"
    assert runtime.registry.get("tester").definition_id == "missing"


def test_parent_may_be_external_but_cannot_be_self() -> None:
    assert make_agent(parent_agent_id="unobserved-lead").parent_agent_id == "unobserved-lead"
    with pytest.raises(ValidationError, match="own parent"):
        make_agent(parent_agent_id="child-1")


@pytest.mark.asyncio
async def test_native_semantic_registration_does_not_erase_existing_process_facts() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    await runtime.apply(
        start(
            make_agent(
                pid=42,
                worktree="/repo",
                branch="feature",
                task="Verify auth",
                definition_id="tester",
            )
        )
    )
    await runtime.apply(
        start(make_agent(role="quality", parent_agent_id="lead"), EventSource.NATIVE, 1)
    )
    agent = runtime.registry.get("child-1")
    assert agent.pid == 42
    assert agent.worktree == "/repo"
    assert agent.branch == "feature"
    assert agent.task == "Verify auth"
    assert agent.role == "quality"


def test_checked_in_example_defines_meaningful_roles() -> None:
    example = Path(__file__).resolve().parents[2] / "config" / "semantic-agents.example.yaml"
    settings = Settings.load(example)
    assert [item.name for item in settings.agents] == [
        "Tester",
        "Reviewer",
        "Researcher",
        "Backend Engineer",
        "Frontend Engineer",
    ]


@pytest.mark.asyncio
async def test_stopping_an_instance_discards_its_semantic_authority() -> None:
    runtime = OfficeRuntime(definitions=AgentDefinitionRegistry(settings_for()))
    await runtime.apply(start(make_agent(name="Native Lead", role="lead"), EventSource.NATIVE))
    await runtime.apply(
        AgentEvent(
            type=AgentEventType.AGENT_STOPPED,
            agent_id="child-1",
            source=EventSource.NATIVE,
            timestamp=NOW + timedelta(seconds=1),
        )
    )
    await runtime.apply(start(make_agent(definition_id="tester"), seconds=2))
    actual = runtime.registry.get("child-1")
    assert actual.name == "Tester"
    assert actual.role == "tester"
    assert actual.responsibilities == TESTER.responsibilities
