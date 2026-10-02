import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime

import psutil

from backend.adapters.base import AgentAdapter
from backend.adapters.generic import GenericProcessAdapter
from backend.config import ObserverSettings
from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.observer.tools import ToolObserver
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
        self._tool_observer = ToolObserver()
        self._observation_tasks: dict[str, asyncio.Task[None]] = {}
        self._tool_tasks: dict[str, asyncio.Task[None]] = {}
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()
        self._initialized = False

    async def run_once(self) -> None:
        if not self._initialized:
            self._managed_ids = {
                agent.id for agent in self.runtime.registry.all() if agent.pid is not None
            }
            self._initialized = True
        detected: dict[str, Agent] = {}
        detected_by: dict[str, AgentAdapter] = {}
        detection_failed = False
        for adapter in self.adapters:
            try:
                for agent in await adapter.detect():
                    detected[agent.id] = agent
                    detected_by[agent.id] = adapter
            except Exception:
                detection_failed = True
                logger.exception(
                    "adapter detection failed",
                    extra={"adapter": type(adapter).__name__},
                )

        for agent_id, agent in detected.items():
            if agent_id not in {item.id for item in self.runtime.registry.all()}:
                await self.runtime.apply(
                    AgentEvent(
                        source=EventSource.PROCESS,
                        type=AgentEventType.AGENT_STARTED,
                        agent_id=agent_id,
                        payload={"agent": agent.model_dump(mode="json")},
                    )
                )
                logger.info("agent started", extra={"agent_id": agent_id})
            if agent_id not in self._observation_tasks:
                self._observation_tasks[agent_id] = asyncio.create_task(
                    self._consume_adapter(detected_by[agent_id], agent),
                    name=f"observe-{agent_id}",
                )
            if agent_id not in self._tool_tasks and agent.pid is not None:
                self._tool_tasks[agent_id] = asyncio.create_task(
                    self._observe_tools(agent),
                    name=f"observe-tools-{agent_id}",
                )

        missing = set() if detection_failed else self._managed_ids - detected.keys()
        still_alive: set[str] = set()
        for agent_id in missing:
            try:
                current = self.runtime.registry.get(agent_id)
                if current.pid is not None and await asyncio.to_thread(
                    psutil.pid_exists, current.pid
                ):
                    still_alive.add(agent_id)
                    continue
                await self.runtime.apply(
                    AgentEvent(
                        type=AgentEventType.AGENT_STOPPED,
                        agent_id=agent_id,
                        source=EventSource.PROCESS,
                        payload={"pid": current.pid},
                    )
                )
                logger.info("agent stopped", extra={"agent_id": agent_id})
            except KeyError:
                pass
            self._tool_observer.forget(agent_id)
            if task := self._observation_tasks.pop(agent_id, None):
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            if task := self._tool_tasks.pop(agent_id, None):
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)

        self._managed_ids = (
            (self._managed_ids | set(detected)) if detection_failed else set(detected) | still_alive
        )
        for agent in detected.values():
            try:
                await self._mark_idle(agent.id)
            except Exception:
                logger.exception("observer failed", extra={"agent_id": agent.id})

    async def _observe_tools(self, agent: Agent) -> None:
        if agent.pid is None:
            return
        interval = self.settings.tool_scan_interval
        while not self._stopped.is_set():
            try:
                events = await asyncio.to_thread(self._tool_observer.scan, agent.id, agent.pid)
                for event in events:
                    try:
                        await self.runtime.apply(event)
                    except KeyError:
                        return
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("tool observation failed", extra={"agent_id": agent.id})
            with suppress(TimeoutError):
                await asyncio.wait_for(self._stopped.wait(), timeout=interval)

    async def _consume_adapter(self, adapter: AgentAdapter, agent: Agent) -> None:
        try:
            async for event in adapter.observe(agent):
                try:
                    await self.runtime.apply(event)
                except KeyError:
                    pass
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("adapter observation failed", extra={"agent_id": agent.id})

    async def _mark_idle(self, agent_id: str) -> None:
        agent = self.runtime.registry.get(agent_id)
        inactive = (datetime.now(UTC) - agent.last_active_at).total_seconds()
        if inactive <= self.settings.idle_timeout:
            return
        if agent.status in {AgentState.IDLE, AgentState.DONE, AgentState.OFFLINE}:
            return
        await self.runtime.apply(
            AgentEvent(
                source=EventSource.TIMEOUT,
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
                await asyncio.wait_for(self._stopped.wait(), timeout=self.settings.scan_interval)

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.run(), name="agent-office-observer")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task
        for task in self._observation_tasks.values():
            task.cancel()
        for task in self._tool_tasks.values():
            task.cancel()
        if self._observation_tasks:
            await asyncio.gather(*self._observation_tasks.values(), return_exceptions=True)
        if self._tool_tasks:
            await asyncio.gather(*self._tool_tasks.values(), return_exceptions=True)
        self._observation_tasks.clear()
        self._tool_tasks.clear()
