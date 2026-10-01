# Agent Office Acceptance Criteria

The phase is complete when all of the following are true.

## Provenance

- AgentEvent has a typed, provider-agnostic source/provenance field.
- Old callers that omit source still validate.
- office-run events are marked as wrapper.
- ToolObserver events are marked as tool_process.
- passive process events are marked as process.
- timeout idle events are marked as timeout.

## Arbitration

- Source priority is defined in one place.
- Runtime status tracks enough provenance to make arbitration deterministic.
- Lower-priority status evidence cannot overwrite a newer, stronger state.
- Stale equal-priority evidence cannot overwrite newer evidence.
- Newer valid equal-priority evidence can update status.
- Timeout IDLE cannot immediately clobber recent TESTING/SEARCHING/TOOL_RUNNING evidence.

## Identity

- A wrapped Codex process with AGENT_OFFICE_ID appears as one agent.
- Generic scanning remains usable for unwrapped supported agents.
- Existing lifecycle start/stop behavior does not regress.

## Compatibility

- Existing WebSocket message types continue to work.
- Existing frontend normalized AgentState behavior still works.
- POST /api/events remains compatible with requests that do not send source.

## Quality

- New arbitration behavior has focused unit tests.
- Existing backend tests pass.
- If frontend code changes, frontend tests pass.
- Python lint passes.
- Frontend lint and production build pass.

## Manual smoke test

With the Agent Office server running:

1. Start a wrapped Codex agent.
2. Confirm only one character appears.
3. Run a search command and observe SEARCHING behavior.
4. Run tests and observe TESTING behavior.
5. Confirm idle timeout does not visually interrupt an active observed tool process.
6. Exit the agent and confirm lifecycle cleanup.
