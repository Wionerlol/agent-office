from datetime import UTC
from typing import Any

from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.observer.tools import state_for_command
from backend.runtime.bus import EventBus
from backend.state.engine import AgentStateEngine
from backend.state.provenance import (
    SOURCE_PRIORITY,
    StatusEvidence,
    accepts_status,
    accepts_stop,
)
from backend.state.registry import AgentRegistry


class OfficeRuntime:
    """Apply normalized events and expose one authoritative live office state."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        bus: EventBus | None = None,
        state_engine: AgentStateEngine | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.bus = bus or EventBus()
        self.state_engine = state_engine or AgentStateEngine()
        self._status_evidence: dict[str, StatusEvidence] = {}
        self._identity_evidence: dict[str, StatusEvidence] = {}

    def status_evidence(self, agent_id: str) -> StatusEvidence:
        agent = self.registry.get(agent_id)
        return self._status_evidence.setdefault(
            agent_id,
            StatusEvidence(
                EventSource.API,
                agent.last_active_at.replace(tzinfo=UTC)
                if agent.last_active_at.tzinfo is None
                else agent.last_active_at,
            ),
        )

    @staticmethod
    def _ignored(agent_id: str) -> dict[str, Any]:
        return {"type": "agent.updated", "agent_id": agent_id, "changes": {}}

    async def apply(self, event: AgentEvent) -> dict[str, Any]:
        if event.type is AgentEventType.AGENT_STARTED:
            agent = Agent.model_validate(event.payload["agent"])
            if agent.id != event.agent_id:
                raise ValueError("Started agent identity must match event agent_id")
            existing = next((item for item in self.registry.all() if item.id == agent.id), None)
            if existing is not None:
                identity = self._identity_evidence.get(agent.id, self.status_evidence(agent.id))
                if (
                    event.timestamp < identity.observed_at
                    or SOURCE_PRIORITY[event.source] < SOURCE_PRIORITY[identity.source]
                ):
                    return self._ignored(agent.id)
                # Discovery/start retries enrich identity without resetting current activity.
                changes = agent.model_dump(
                    exclude={
                        "status",
                        "last_active_at",
                        "started_at",
                        "current_tool",
                        "changed_files",
                        "metadata",
                    }
                )
                changes["metadata"] = {**existing.metadata, **agent.metadata}
                self.registry.update(agent.id, **changes)
                self._identity_evidence[agent.id] = StatusEvidence(event.source, event.timestamp)
                message: dict[str, Any] = {
                    "type": "agent.updated",
                    "agent_id": agent.id,
                    "changes": changes,
                }
            else:
                self.registry.add(agent)
                evidence = StatusEvidence(event.source, event.timestamp)
                self._status_evidence[agent.id] = evidence
                self._identity_evidence[agent.id] = evidence
                message = {"type": "agent.started", "agent": agent.model_dump(mode="json")}
        elif event.type is AgentEventType.AGENT_STOPPED:
            if not any(agent.id == event.agent_id for agent in self.registry.all()):
                return {"type": "agent.stopped", "agent_id": event.agent_id}
            current = self.registry.get(event.agent_id)
            if event.payload.get("pid") is not None and event.payload["pid"] != current.pid:
                return self._ignored(event.agent_id)
            status = self.status_evidence(event.agent_id)
            identity = self._identity_evidence.get(event.agent_id, status)
            if not (
                accepts_stop(status, event.source, event.timestamp)
                and event.timestamp >= identity.observed_at
            ):
                return self._ignored(event.agent_id)
            self.registry.remove(event.agent_id)
            self._status_evidence.pop(event.agent_id, None)
            self._identity_evidence.pop(event.agent_id, None)
            message = {"type": "agent.stopped", "agent_id": event.agent_id}
        else:
            message = self._apply_update(event)

        if message.get("changes") != {}:
            await self.bus.publish(message)
        return message

    def _apply_update(self, event: AgentEvent) -> dict[str, Any]:
        current = self.registry.get(event.agent_id)
        status_event = event.type in {
            AgentEventType.STATE_CHANGED,
            AgentEventType.TOOL_STARTED,
            AgentEventType.TOOL_FINISHED,
            AgentEventType.ERROR,
        }
        if status_event:
            evidence = self.status_evidence(event.agent_id)
            is_offline = (
                event.type is AgentEventType.STATE_CHANGED
                and event.payload["to"] == AgentState.OFFLINE
            )
            accepted = (
                accepts_stop(evidence, event.source, event.timestamp)
                if is_offline
                else accepts_status(current.status, evidence, event.source, event.timestamp)
            )
            if not accepted:
                return self._ignored(event.agent_id)
        active_at = current.last_active_at
        if active_at.tzinfo is None:
            active_at = active_at.replace(tzinfo=UTC)
        changes: dict[str, Any] = {"last_active_at": max(active_at, event.timestamp)}

        if event.type is AgentEventType.STATE_CHANGED:
            changes["status"] = AgentState(event.payload["to"])
        elif event.type is AgentEventType.FILE_CHANGED:
            path = str(event.payload["file"])
            changes["changed_files"] = list(dict.fromkeys([*current.changed_files, path]))
        elif event.type is AgentEventType.TASK_UPDATED:
            changes["task"] = event.payload.get("task")
        elif event.type is AgentEventType.TOOL_STARTED:
            changes["current_tool"] = event.payload.get("next_tool", event.payload.get("tool"))
            command = event.payload.get("command") or event.payload.get("tool") or ""
            if isinstance(command, list) and all(isinstance(part, str) for part in command):
                changes["status"] = state_for_command(command)
            else:
                changes["status"] = state_for_command(str(command))
            if "next_state" in event.payload:
                changes["status"] = AgentState(event.payload["next_state"])
        elif event.type is AgentEventType.TOOL_FINISHED:
            changes["current_tool"] = event.payload.get("next_tool")
            changes["status"] = AgentState(event.payload.get("next_state", AgentState.THINKING))
        elif event.type is AgentEventType.ERROR:
            changes["status"] = AgentState.ERROR
            changes["metadata"] = {**current.metadata, "last_error": event.payload.get("message")}

        if "status" in changes:
            expected = (
                event.payload.get("from") if event.type is AgentEventType.STATE_CHANGED else None
            )
            changes["status"] = self.state_engine.transition(
                current.status, changes["status"], expected
            )
            if changes["status"] in {AgentState.DONE, AgentState.ERROR, AgentState.OFFLINE}:
                changes["current_tool"] = None
        updated = self.registry.update(event.agent_id, **changes)
        if status_event:
            self._status_evidence[event.agent_id] = StatusEvidence(event.source, event.timestamp)
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
            if "current_tool" in changes and current.current_tool is not None:
                serialized["current_tool"] = updated.current_tool
        return {"type": "agent.updated", "agent_id": event.agent_id, "changes": serialized}
