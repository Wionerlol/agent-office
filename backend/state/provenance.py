"""Central authority policy for normalized runtime evidence."""

from dataclasses import dataclass
from datetime import datetime

from backend.models import AgentState, EventSource

SOURCE_PRIORITY = {
    EventSource.NATIVE: 80,
    EventSource.WRAPPER: 70,
    EventSource.API: 60,
    EventSource.TOOL_PROCESS: 50,
    EventSource.FILESYSTEM: 40,
    EventSource.GIT: 30,
    EventSource.PROCESS: 20,
    EventSource.TIMEOUT: 10,
}
BASELINE_STATES = {AgentState.STARTING, AgentState.THINKING, AgentState.IDLE}
LIFECYCLE_SOURCES = {EventSource.NATIVE, EventSource.WRAPPER, EventSource.API, EventSource.PROCESS}


@dataclass(frozen=True)
class StatusEvidence:
    source: EventSource
    observed_at: datetime


def accepts_status(
    current: AgentState,
    evidence: StatusEvidence,
    source: EventSource,
    timestamp: datetime,
) -> bool:
    if timestamp < evidence.observed_at:
        return False
    # Baseline states describe absence of specific activity. Native facts remain explicit.
    if current in BASELINE_STATES and evidence.source is not EventSource.NATIVE:
        return True
    return SOURCE_PRIORITY[source] >= SOURCE_PRIORITY[evidence.source]


def accepts_stop(evidence: StatusEvidence, source: EventSource, timestamp: datetime) -> bool:
    # Actual process death is authoritative even when activity came from a stronger source.
    return source in LIFECYCLE_SOURCES and timestamp >= evidence.observed_at
