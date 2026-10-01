import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import psutil

from backend.adapters.base import AgentAdapter
from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.observer.process import ProcessObserver, ProcessSnapshot

KNOWN_PROVIDERS = frozenset({"codex", "claude", "opencode"})


class GenericProcessAdapter(AgentAdapter):
    def __init__(
        self,
        pids: list[int] | None = None,
        command_names: set[str] | None = None,
        provider: str | None = None,
        scan_interval: float = 1.0,
    ) -> None:
        self.command_names = command_names if command_names is not None else KNOWN_PROVIDERS
        command_hints = (
            None
            if pids is not None or not self.command_names
            else {*self.command_names, "office-run"}
        )
        self.processes = ProcessObserver(pids, command_hints=command_hints)
        self.provider = provider
        self.scan_interval = scan_interval

    async def detect(self) -> list[Agent]:
        detected: list[tuple[ProcessSnapshot, Agent]] = []
        for process in await asyncio.to_thread(self.processes.snapshots):
            if agent := self._to_agent(process):
                detected.append((process, agent))
        parent_pids = {process.parent_pid for process, _ in detected}
        # Wrapped descendants inherit the same ID. Observe their oldest/root process,
        # not a nested tool that may exit while the wrapped agent is still alive.
        explicit: dict[str, Agent] = {}
        fallback: list[Agent] = []
        for process, agent in sorted(detected, key=lambda item: (item[0].created_at, item[0].pid)):
            if process.environment.get("AGENT_OFFICE_ID"):
                explicit.setdefault(agent.id, agent)
            elif process.pid not in parent_pids:
                fallback.append(agent)
        return [*explicit.values(), *fallback]

    async def observe(self, agent: Agent) -> AsyncIterator[AgentEvent]:
        if agent.pid is None:
            return
        never = asyncio.Event()
        while await asyncio.to_thread(psutil.pid_exists, agent.pid):
            try:
                await asyncio.wait_for(never.wait(), timeout=self.scan_interval)
            except TimeoutError:
                continue
        yield AgentEvent(
            type=AgentEventType.AGENT_STOPPED,
            agent_id=agent.id,
            source=EventSource.PROCESS,
            payload={"pid": agent.pid},
        )

    def _to_agent(self, process: ProcessSnapshot) -> Agent | None:
        environment = process.environment
        executable = Path(process.command[0]).name.lower()
        command_names = {Path(part).name.lower() for part in process.command}
        matched = next((name for name in self.command_names if name in command_names), None)
        provider = (
            environment.get("AGENT_OFFICE_PROVIDER") or self.provider or matched or executable
        )
        explicit = environment.get("AGENT_OFFICE_ID")
        if not explicit and ("app-server" in process.command or "office-run" in command_names):
            return None
        if not explicit and matched is None:
            return None
        if self.provider and provider != self.provider and matched is None:
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


class CustomAgentAdapter(GenericProcessAdapter):
    """Detect only explicitly tagged custom processes."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(command_names=set(), provider="custom", **kwargs)
