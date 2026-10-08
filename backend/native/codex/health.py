"""Integration diagnostics, independent of AgentState and native free text."""

from dataclasses import dataclass
from enum import StrEnum


class NativeHealth(StrEnum):
    DISABLED = "disabled"
    UNBOUND = "unbound"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DEGRADED = "degraded"
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class NativeFailure:
    scope: str
    category: str
    failure_type: str
