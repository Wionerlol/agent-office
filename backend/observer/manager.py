import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime

from backend.adapters.base import AgentAdapter
from backend.adapters.generic import GenericProcessAdapter
from backend.config import ObserverSettings
from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.observer.filesystem import FileSystemObserver
from backend.observer.git import GitObserver
from backend.runtime.office import OfficeRuntime

logger = logging.getLogger(__name__)


class ObserverManager:
    """Coordinate fallible observers without allowing one failure to stop the server."""

    def __init__(
        self,
        runtime: OfficeRuntime,
        settings: ObserverSettings,
        adapters: list[AgentAdapter] | None = None,
    ) -> None:
        self.runtime = runtime
        self.settings = settings
        self.adapters = adapters or [GenericProcessAdapter(scan_interval=settings.scan_interval)]
        self._managed_ids: set[str] = set()
        self._filesystems: dict[str, FileSystemObserver] = {}
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    async def run_once(self) -> None:
        detected: dict[str, Agent] = {}
        for adapter in self.adapters:
            try:
                detected.update({agent.id: agent for agent in await adapter.detect()})
            except Exception:
                logger.exception(
                    "adapter detection failed",
                    extra={"adapter": type(adapter).__name__},
                )

        for agent_id, agent in detected.items():
            if agent_id not in self._managed_ids:
                await self.runtime.apply(
                    AgentEvent(
                        type=AgentEventType.AGENT_STARTED,
                        agent_id=agent_id,
                        payload={"agent": agent.model_dump(mode="json")},
                    )
                )
                logger.info("agent started", extra={"agent_id": agent_id})

        for agent_id in self._managed_ids - detected.keys():
            try:
                await self.runtime.apply(
                    AgentEvent(type=AgentEventType.AGENT_STOPPED, agent_id=agent_id)
                )
                logger.info("agent stopped", extra={"agent_id": agent_id})
            except KeyError:
                pass

        self._managed_ids = set(detected)
        for agent in detected.values():
            try:
                await self._observe_repository(agent)
                await self._mark_idle(agent.id)
            except Exception:
                logger.exception("observer failed", extra={"agent_id": agent.id})

    async def _observe_repository(self, agent: Agent) -> None:
        git = GitObserver(agent.repository).snapshot()
        current = self.runtime.registry.get(agent.id)
        facts: dict[str, object] = {}
        if current.branch != git.branch:
            facts["branch"] = git.branch
        if current.worktree != git.worktree:
            facts["worktree"] = git.worktree
        if facts:
            self.runtime.registry.update(agent.id, **facts)
            await self.runtime.bus.publish(
                {"type": "agent.updated", "agent_id": agent.id, "changes": facts}
            )

        filesystem = self._filesystems.setdefault(
            agent.id, FileSystemObserver(agent.repository)
        )
        for event in filesystem.scan(agent.id):
            await self.runtime.apply(event)
            current = self.runtime.registry.get(agent.id)
            if current.status not in {AgentState.TESTING, AgentState.TOOL_RUNNING}:
                await self.runtime.apply(
                    AgentEvent(
                        type=AgentEventType.STATE_CHANGED,
                        agent_id=agent.id,
                        payload={"from": current.status, "to": AgentState.CODING},
                    )
                )

    async def _mark_idle(self, agent_id: str) -> None:
        agent = self.runtime.registry.get(agent_id)
        inactive = (datetime.now(UTC) - agent.last_active_at).total_seconds()
        if inactive <= self.settings.idle_timeout:
            return
        if agent.status in {AgentState.IDLE, AgentState.DONE, AgentState.OFFLINE}:
            return
        await self.runtime.apply(
            AgentEvent(
                type=AgentEventType.STATE_CHANGED,
                agent_id=agent.id,
                payload={"from": agent.status, "to": AgentState.IDLE},
            )
        )

    async def run(self) -> None:
        self._stopped.clear()
        while not self._stopped.is_set():
            await self.run_once()
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stopped.wait(), timeout=self.settings.scan_interval
                )

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run(), name="agent-office-observer")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task
