"""Project-scoped semantic identity, independent of activity arbitration."""

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import Any

from backend.config import Settings
from backend.models import Agent, AgentDefinition, EventSource

SEMANTIC_FIELDS = ("name", "role", "responsibilities", "parent_agent_id", "definition_id")


class IdentityAuthority(IntEnum):
    PROCESS = 1
    WRAPPER = 2
    DEFINITION = 3
    NATIVE = 4


@dataclass(frozen=True)
class IdentityEvidence:
    authority: IdentityAuthority
    observed_at: datetime


class AgentDefinitionRegistry:
    def __init__(self, settings: Settings | None = None) -> None:
        self._projects: dict[str, dict[str, AgentDefinition]] = {}
        if settings is None:
            return
        groups = [(settings.project.path, [*settings.agents, *settings.project.agents])]
        groups.extend((project.path, project.agents) for project in settings.projects)
        for path, definitions in groups:
            project = self._projects.setdefault(os.path.abspath(path), {})
            for definition in definitions:
                if definition.id in project:
                    raise ValueError(f"Duplicate agent definition: {definition.id} in {path}")
                project[definition.id] = definition.model_copy(deep=True)

    def match(self, agent: Agent) -> AgentDefinition | None:
        # Explicit selectors do not silently match a different definition if unknown.
        identifier = agent.definition_id or agent.id
        for path in (agent.repository, agent.worktree):
            if path and identifier in self._projects.get(os.path.abspath(path), {}):
                return self._projects[os.path.abspath(path)][identifier]
        return None


def responsibilities_from_environment(environment: Mapping[str, str]) -> list[str]:
    """Decode transport metadata only; observers do not choose semantic authority."""
    try:
        value = json.loads(environment.get("AGENT_OFFICE_RESPONSIBILITIES", "[]"))
    except (ValueError, TypeError):
        return []
    return value if isinstance(value, list) and all(isinstance(item, str) for item in value) else []


class SemanticIdentityResolver:
    def __init__(self, definitions: AgentDefinitionRegistry | None = None) -> None:
        self.definitions = definitions or AgentDefinitionRegistry()
        self._evidence: dict[str, dict[str, IdentityEvidence]] = {}

    def forget(self, agent_id: str) -> None:
        self._evidence.pop(agent_id, None)

    def resolve(
        self,
        incoming: Agent,
        source: EventSource,
        timestamp: datetime,
        current: Agent | None = None,
    ) -> Agent:
        authority = IdentityAuthority.PROCESS
        if source is EventSource.NATIVE:
            authority = IdentityAuthority.NATIVE
        elif source in {EventSource.WRAPPER, EventSource.API} or incoming.metadata.get("wrapped"):
            authority = IdentityAuthority.WRAPPER

        evidence = self._evidence.setdefault(incoming.id, {})
        values: dict[str, Any] = {}
        for field in SEMANTIC_FIELDS:
            value = getattr(incoming, field)
            field_authority = (
                IdentityAuthority.PROCESS
                if field == "name" and incoming.metadata.get("name_is_generated") is True
                else authority
            )
            if value:
                previous = evidence.get(field)
                if previous is None or (
                    field_authority >= previous.authority and timestamp >= previous.observed_at
                ):
                    values[field] = value
                    evidence[field] = IdentityEvidence(field_authority, timestamp)

        candidate = (current or incoming).model_copy(update=values)
        definition = self.definitions.match(candidate)
        if definition:
            defaults = definition.model_dump(exclude={"id"})
            defaults["definition_id"] = definition.id
            for field, value in defaults.items():
                # Null role is absence of a definition default, not a command to clear a role.
                if value is None:
                    continue
                previous = evidence.get(field)
                if previous is None or previous.authority <= IdentityAuthority.DEFINITION:
                    values[field] = value
                    evidence[field] = IdentityEvidence(IdentityAuthority.DEFINITION, timestamp)
        return Agent.model_validate((current or incoming).model_copy(update=values))
