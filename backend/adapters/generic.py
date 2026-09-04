import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import psutil

from backend.adapters.base import AgentAdapter
from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.observer.process import ProcessObserver, ProcessSnapshot

KNOWN_PROVIDERS = {"codex", "claude", "opencode"}


class GenericProcessAdapter(AgentAdapter):
    def __init__(
        self,
        pids: list[int] | None = None,
        command_names: set[str] | None = None,
        provider: str | None = None,
        scan_interval: float = 1.0,
    ) -> None:
        self.processes = ProcessObserver(pids)
        self.command_names = command_names or KNOWN_PROVIDERS
        self.provider = provider
        self.scan_interval = scan_interval

    async def detect(self) -> list[Agent]:
        agents: list[Agent] = []
        for process in self.processes.snapshots():
            if agent := self._to_agent(process):
                agents.append(agent)
        return agents

    async def observe(self, agent: Agent) -> AsyncIterator[AgentEvent]:
        if agent.pid is None:
            return
        try:
            await asyncio.to_thread(psutil.Process(agent.pid).wait)
        except psutil.NoSuchProcess:
            pass
        yield AgentEvent(type=AgentEventType.AGENT_STOPPED, agent_id=agent.id)

    def _to_agent(self, process: ProcessSnapshot) -> Agent | None:
        environment = process.environment
        executable = Path(process.command[0]).name.lower()
        provider = environment.get("AGENT_OFFICE_PROVIDER") or self.provider or executable
        explicit = environment.get("AGENT_OFFICE_ID")
        if not explicit and executable not in self.command_names:
            return None
        if self.provider and provider != self.provider and executable not in self.command_names:
            return None
        repository = environment.get("AGENT_OFFICE_REPOSITORY", process.cwd)
        created = datetime.fromtimestamp(process.created_at, tz=UTC)
        return Agent(
            id=explicit or f"{provider}-{process.pid}",
            name=environment.get("AGENT_OFFICE_NAME", f"{provider.title()} {process.pid}"),
            provider=provider,
            pid=process.pid,
            repository=repository,
            worktree=environment.get("AGENT_OFFICE_WORKTREE"),
            branch=environment.get("AGENT_OFFICE_BRANCH"),
            status=AgentState.STARTING,
            task=environment.get("AGENT_OFFICE_TASK"),
            role=environment.get("AGENT_OFFICE_ROLE"),
            started_at=created,
            last_active_at=created,
            metadata={"command": process.command},
        )
