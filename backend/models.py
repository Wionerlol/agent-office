from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class AgentState(StrEnum):
    STARTING = "starting"
    THINKING = "thinking"
    CODING = "coding"
    TOOL_RUNNING = "tool_running"
    TESTING = "testing"
    SEARCHING = "searching"
    WAITING = "waiting"
    IDLE = "idle"
    ERROR = "error"
    DONE = "done"
    OFFLINE = "offline"


class Agent(BaseModel):
    id: str
    name: str
    provider: str
    pid: int | None = None
    repository: str
    worktree: str | None = None
    branch: str | None = None
    status: AgentState = AgentState.STARTING
    task: str | None = None
    role: str | None = None
    current_tool: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    last_active_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentEventType(StrEnum):
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    STATE_CHANGED = "agent.state_changed"
    TOOL_STARTED = "agent.tool_started"
    TOOL_FINISHED = "agent.tool_finished"
    FILE_CHANGED = "agent.file_changed"
    TASK_UPDATED = "agent.task_updated"
    ERROR = "agent.error"


class AgentEvent(BaseModel):
    type: AgentEventType
    agent_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class ProjectInfo(BaseModel):
    name: str
    path: str
    branch: str | None = None
