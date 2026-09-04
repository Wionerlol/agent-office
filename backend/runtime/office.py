from typing import Any

from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.runtime.bus import EventBus
from backend.runtime.storage import EventStorage
from backend.state.registry import AgentRegistry


class OfficeRuntime:
    """Apply normalized events and expose one authoritative live office state."""

    def __init__(
        self,
        storage: EventStorage,
        registry: AgentRegistry | None = None,
        bus: EventBus | None = None,
    ) -> None:
        self.storage = storage
        self.registry = registry or AgentRegistry()
        self.bus = bus or EventBus()

    async def apply(self, event: AgentEvent, *, record: bool = True) -> dict[str, Any]:
        if event.type is AgentEventType.AGENT_STARTED:
            agent = Agent.model_validate(event.payload["agent"])
            self.registry.add(agent)
            message: dict[str, Any] = {
                "type": "agent.started",
                "agent": agent.model_dump(mode="json"),
            }
        elif event.type is AgentEventType.AGENT_STOPPED:
            self.registry.remove(event.agent_id)
            message = {"type": "agent.stopped", "agent_id": event.agent_id}
        else:
            message = self._apply_update(event)

        if record:
            self.storage.append(event)
        await self.bus.publish(message)
        return message

    def _apply_update(self, event: AgentEvent) -> dict[str, Any]:
        current = self.registry.get(event.agent_id)
        changes: dict[str, Any] = {"last_active_at": event.timestamp}

        if event.type is AgentEventType.STATE_CHANGED:
            changes["status"] = AgentState(event.payload["to"])
        elif event.type is AgentEventType.FILE_CHANGED:
            path = str(event.payload["file"])
            changes["changed_files"] = list(dict.fromkeys([*current.changed_files, path]))
        elif event.type is AgentEventType.TASK_UPDATED:
            changes["task"] = event.payload.get("task")
        elif event.type is AgentEventType.TOOL_STARTED:
            changes["current_tool"] = event.payload.get("tool")
            changes["status"] = AgentState.TOOL_RUNNING
        elif event.type is AgentEventType.TOOL_FINISHED:
            changes["current_tool"] = None
            changes["status"] = AgentState(event.payload.get("next_state", AgentState.THINKING))
        elif event.type is AgentEventType.ERROR:
            changes["status"] = AgentState.ERROR
            changes["metadata"] = {**current.metadata, "last_error": event.payload.get("message")}

        updated = self.registry.update(event.agent_id, **changes)
        serialized = {}
        for key, value in changes.items():
            if isinstance(value, AgentState):
                serialized[key] = value.value
            elif hasattr(value, "isoformat"):
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        if event.type is AgentEventType.STATE_CHANGED:
            serialized = {"status": updated.status.value}
        return {"type": "agent.updated", "agent_id": event.agent_id, "changes": serialized}

    async def restore(self) -> None:
        for event in self.storage.read():
            try:
                await self.apply(event, record=False)
            except KeyError:
                continue
