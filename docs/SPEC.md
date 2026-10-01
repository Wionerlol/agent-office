# Agent Office Implementation Spec

## Scope

Implement the next reliability phase for Agent Office: improve state fidelity without rewriting the rendering system.

The implementation must preserve the existing architecture:
- Python/FastAPI backend;
- normalized Agent/AgentEvent domain model;
- OfficeRuntime as authoritative live state;
- WebSocket snapshot + incremental updates;
- React/Zustand/PixiJS frontend;
- current office state-to-visual mapping.

Do not redesign the UI unless a backend change requires a minimal frontend representation.

## Primary objective

Introduce event provenance and source priority so lower-confidence heuristics cannot overwrite newer or more authoritative runtime facts.

## Required domain additions

Add a provider-agnostic event source model.

Recommended shape:

```python
class EventSource(StrEnum):
    NATIVE = "native"
    WRAPPER = "wrapper"
    TOOL_PROCESS = "tool_process"
    FILESYSTEM = "filesystem"
    GIT = "git"
    PROCESS = "process"
    TIMEOUT = "timeout"
    API = "api"
```

Each `AgentEvent` should carry source/provenance. Prefer an explicit field over burying it in payload.

Recommended:

```python
class AgentEvent(BaseModel):
    type: AgentEventType
    agent_id: str
    timestamp: datetime
    source: EventSource = EventSource.API
    payload: dict[str, Any]
```

Backward compatibility is required for callers that omit `source`.

## Source priority

Centralize source precedence in one backend module. Do not duplicate precedence rules across observers.

Initial ordering, highest to lowest:

1. native agent event
2. office-run wrapper event
3. tool process observation
4. filesystem observation
5. git observation
6. generic process observation
7. timeout heuristic

The API/default source should be handled deliberately rather than accidentally. External manually posted events should not automatically outrank trusted runtime-native events unless explicitly designed to do so.

Implementation may use integer ranks, but the policy must have named sources and tests.

## State arbitration

For every status-affecting event, OfficeRuntime must decide whether the incoming event is allowed to change the authoritative state.

At minimum consider:
- source priority;
- event timestamp;
- current authoritative source;
- whether the transition is lifecycle-critical;
- whether the event is a terminal/offline lifecycle event.

Store enough metadata per agent to explain the current state source. This may be internal runtime metadata or part of Agent metadata, but it must be testable.

Recommended runtime facts:

```text
status
status_source
status_observed_at
```

Do not let an old high-priority event overwrite a newer high-priority event.

Do not let a low-priority timeout-derived IDLE overwrite a recent TOOL_PROCESS TESTING state.

## Lifecycle rules

Lifecycle events require special handling.

- `agent.started` may create/register an agent.
- duplicate discovery of the same logical office-run agent must not create a second visible agent.
- wrapper-created identity should be preferred when `AGENT_OFFICE_ID` exists.
- `agent.stopped` from the authoritative process lifecycle should remove/offline the correct agent.
- passive process scanning is fallback discovery, not a competing identity authority.

Preserve existing process de-duplication behavior and strengthen it where needed.

## Observer responsibilities

### Wrapper

`office-run` should explicitly tag events as `wrapper`.

It remains the preferred lifecycle identity bridge for wrapped agents.

### ToolObserver

Tool events must be tagged as `tool_process`.

Existing command classification remains:
- tests -> TESTING;
- search commands -> SEARCHING;
- other child tools -> TOOL_RUNNING.

### GenericProcessAdapter

Events from passive discovery should be tagged as `process`.

Its role is fallback detection and process lifecycle observation.

### Idle timeout

Idle transitions emitted by ObserverManager must be tagged as `timeout`.

Idle timeout must not clobber a recent stronger state.

## Optional filesystem observer

A filesystem observer is useful for CODING fidelity but is secondary to getting provenance/arbitration correct.

If implemented in this phase:
- watch only the agent repository/worktree;
- ignore generated/noisy paths such as .git, node_modules, dist, build caches, virtualenvs, and runtime logs;
- coalesce bursts;
- emit FILE_CHANGED with source `filesystem`;
- optionally derive CODING only if the arbitration policy accepts that source.

Do not add a heavy dependency or complex event pipeline unless justified.

## WebSocket/API compatibility

The existing WebSocket message protocol should remain compatible:
- snapshot
- agent.started
- agent.updated
- agent.stopped

It is acceptable for `agent.updated.changes` to expose provenance fields if useful, but the frontend must not be forced to understand provider-specific information.

POST /api/events must continue to accept old payloads with no explicit source.

## Frontend

No broad visual redesign.

If status provenance is exposed, it may optionally appear in AgentPanel for diagnostics.

The office scene should continue to react only to normalized AgentState.

## Configuration

Any new heuristic timing/coalescing values must be configurable with safe defaults.

Avoid introducing configuration that is not currently needed.

## Tests

Backend tests must cover:
- default source compatibility;
- source priority ordering;
- lower-priority stale state rejected/ignored;
- newer equal-priority state accepted;
- timeout IDLE not overriding a recent stronger activity state;
- wrapped process identity does not duplicate;
- wrapper lifecycle events carry correct source;
- ToolObserver events carry correct source;
- generic process events carry correct source;
- existing state transition tests remain valid.

Frontend tests are only required if frontend behavior changes.

## Verification

Run:

```bash
uv run pytest
uv run ruff check backend main.py

cd frontend
npm test
npm run lint
npm run build
```

Do not declare completion unless all relevant checks pass.
