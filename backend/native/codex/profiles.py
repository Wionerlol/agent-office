"""Reviewed experimental protocol contracts; upgrades require an explicit profile review."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtocolProfile:
    versions: tuple[str, ...]
    schema: str
    read_methods: frozenset[str]
    fact_methods: frozenset[str]
    item_types: frozenset[str]
    thread_states: frozenset[str] = frozenset({"active", "idle"})
    turn_states: frozenset[str] = frozenset({"inProgress", "completed", "failed", "interrupted"})


PAGINATED_V1 = ProtocolProfile(
    versions=("0.159.3", "0.160.0", "0.160.1", "0.161.0"),
    schema="paginated-thread-items-v1",
    read_methods=frozenset(
        {"initialize", "thread/read", "thread/resume", "thread/turns/list", "thread/items/list"}
    ),
    fact_methods=frozenset(
        {
            "item/tool/requestUserInput",
            "serverRequest/resolved",
            "thread/status/changed",
            "turn/started",
            "turn/completed",
            "item/started",
            "item/completed",
        }
    ),
    item_types=frozenset(
        {"commandExecution", "fileChange", "subAgentActivity", "collabAgentToolCall"}
    ),
)
PROFILES = {version: PAGINATED_V1 for version in PAGINATED_V1.versions}


def profile_for(version: str) -> ProtocolProfile | None:
    return PROFILES.get(version)
