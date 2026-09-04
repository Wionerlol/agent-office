from collections.abc import Iterable

from backend.models import Agent


class AgentRegistry:
    """Owns the current, normalized view of all active agents."""

    def __init__(self, agents: Iterable[Agent] = ()) -> None:
        self._agents = {agent.id: agent.model_copy(deep=True) for agent in agents}

    def add(self, agent: Agent) -> Agent:
        self._agents[agent.id] = agent.model_copy(deep=True)
        return self._agents[agent.id]

    def get(self, agent_id: str) -> Agent:
        try:
            return self._agents[agent_id]
        except KeyError as error:
            raise KeyError(f"Unknown agent: {agent_id}") from error

    def update(self, agent_id: str, **changes: object) -> Agent:
        current = self.get(agent_id)
        updated = current.model_copy(update=changes)
        self._agents[agent_id] = Agent.model_validate(updated)
        return self._agents[agent_id]

    def remove(self, agent_id: str) -> Agent:
        try:
            return self._agents.pop(agent_id)
        except KeyError as error:
            raise KeyError(f"Unknown agent: {agent_id}") from error

    def all(self) -> list[Agent]:
        return sorted(self._agents.values(), key=lambda agent: (agent.started_at, agent.id))

    def clear(self) -> None:
        self._agents.clear()
