from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

PERSONALITIES = ("Focused", "Curious", "Steady", "Methodical", "Bold")


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


class AgentDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str | None = None
    responsibilities: list[str] = Field(default_factory=list)


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
    responsibilities: list[str] = Field(default_factory=list)
    parent_agent_id: str | None = None
    definition_id: str | None = None
    current_tool: str | None = None
    changed_files: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    last_active_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parent(self) -> Self:
        if self.parent_agent_id == self.id:
            raise ValueError("An agent cannot be its own parent")
        return self

    @model_validator(mode="after")
    def add_default_personality(self) -> Self:
        if "personality" not in self.metadata:
            index = sum(ord(character) for character in self.id) % len(PERSONALITIES)
            self.metadata = {**self.metadata, "personality": PERSONALITIES[index]}
        return self


class AgentEventType(StrEnum):
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"
    STATE_CHANGED = "agent.state_changed"
    TOOL_STARTED = "agent.tool_started"
    TOOL_FINISHED = "agent.tool_finished"
    FILE_CHANGED = "agent.file_changed"
    TASK_UPDATED = "agent.task_updated"
    ERROR = "agent.error"


class EventSource(StrEnum):
    NATIVE = "native"
    WRAPPER = "wrapper"
    TOOL_PROCESS = "tool_process"
    FILESYSTEM = "filesystem"
    GIT = "git"
    PROCESS = "process"
    TIMEOUT = "timeout"
    API = "api"


class AgentEvent(BaseModel):
    type: AgentEventType
    agent_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    source: EventSource = EventSource.API
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ProjectInfo(BaseModel):
    name: str
    path: str
    branch: str | None = None


class CodexUsageWindow(BaseModel):
    used_percent: float = Field(ge=0, le=100)
    remaining_percent: float = Field(ge=0, le=100)
    window_minutes: int = Field(gt=0)
    resets_at: datetime


class CodexUsage(BaseModel):
    status: Literal["available", "unavailable"]
    remaining_percent: float | None = Field(default=None, ge=0, le=100)
    limiting_window: str | None = None
    primary: CodexUsageWindow | None = None
    secondary: CodexUsageWindow | None = None
    individual: CodexUsageWindow | None = None
    plan_type: str | None = None
    updated_at: datetime | None = None
