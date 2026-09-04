from backend.models import AgentState


class StateTransitionError(ValueError):
    """Raised when an event is stale or attempts to revive an offline agent."""


class AgentStateEngine:
    """Validate non-linear agent transitions against the authoritative current state."""

    def transition(
        self,
        current: AgentState,
        target: AgentState | str,
        expected: AgentState | str | None = None,
    ) -> AgentState:
        target_state = AgentState(target)
        if expected is not None and AgentState(expected) is not current:
            raise StateTransitionError(
                f"Stale transition: expected {expected}, current state is {current}"
            )
        if current is AgentState.OFFLINE and target_state is not AgentState.STARTING:
            raise StateTransitionError("Offline agents must restart before changing state")
        return target_state
