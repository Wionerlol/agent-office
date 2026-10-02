# Agent Office Implementation Spec

## Phase state and diagnostic contract

| Phase | State |
| --- | --- |
| 1 State Fidelity | COMPLETE |
| 2 Semantic Agent Model | COMPLETE |
| 3A Native Runtime Capability Probe | COMPLETE |
| 3B Native Adapter | NOT YET IMPLEMENTED |

`backend/probe/` provides opt-in capture, experiment and selected-thread observe commands. It has no live startup hook, API endpoint, frontend protocol, AgentState addition or AgentEvent normalization. It does not replace EventSource, status arbitration, SemanticIdentityResolver, definitions or current OfficeScene routing.

Capture explicitly selected exec/app-server/rollout JSONL through a strict content-denying projector. Records include receipt sequence, UTC receipt timestamp, optional provider timestamp/ordinal, provider, pseudonymized session/request IDs, original event discriminator, diagnostic source string and projected payload. Nested native item/status/relationship structure remains intact. IDs are stable pseudonyms; workspace paths are relative; free text, arguments, outputs, diffs and credentials are hidden; unknown fields are dropped. Only sanitized output is written to ignored runtime/probe files, created exclusively with mode 0600.

Observe connects by Unix WebSocket to a specified loaded native thread. Verify workspace and loaded status before subscription. Use initialize/initialized and thread/resume(excludeTurns=true), without config/input overrides, then scope to the root and explicitly reported children. Never answer server requests or start/interrupt turns on this path. Closing a diagnostic socket does not signal lifecycle death. The standalone experiment command alone drives its own controlled model turns and answers its fixture question after recording real waiting.

The probe is a bounded diagnostic projection, not a lossless archive or the permanent office protocol. Replayed pending requests, nullable metadata, absent timestamps, CLI/daemon version differences and unrecognized fields must remain visible as limits. Missing native sources fail the explicit diagnostic command without affecting normal Agent Office/Codex execution.

The [capability matrix](runtime-probe/CAPABILITY_MATRIX.md), [source guide](runtime-probe/CODEX.md), [DevRouter report](runtime-probe/DEVROUTER.md) and [observed samples](runtime-probe/SAMPLES.md) are the Phase 3A evidence. Exact native input-wait facts remain distinct from generic WAITING. Native subagent identity/parentage must never be fabricated from OS children. Existing command classification is process/structured observation, not a native TESTING or SEARCHING state. No native adapter, filesystem CODING detection, prompt NLP, role layout, org chart or database is included.

## Completed Phase 2: Semantic Agent Model

State Fidelity is complete. Its contract below remains authoritative for activity arbitration. Semantic identity is resolved independently; tool/state events never assign roles.

### Domain

`AgentDefinition` contains `id`, `name`, optional free-form `role`, and `responsibilities` (a fresh empty list by default). `Agent` retains every existing field and adds `responsibilities=[]`, `parent_agent_id=None`, and `definition_id=None`; existing `role` remains stable responsibility. Task, status, and current_tool keep their meanings. A non-null parent ID identifies a subagent. Parent IDs may reference agents outside the current snapshot; self-parent references are invalid. No organization graph or cascade deletion is implemented.

### Project registry

The existing office YAML accepts top-level `agents`, scoped to `project.path`, and optional `agents` inside each `projects` entry (or the primary `project`). Definitions are loaded once with server configuration. IDs must be unique within a repository, including definitions distributed across duplicate project-path entries; different projects may reuse an ID. No filesystem scanning, hot reload, database, or global name guessing is added.

Match exact `definition_id` when present, otherwise exact runtime `id`, first by repository and then by the registered worktree root. An explicit unknown selector preserves fallback identity rather than matching another definition. Multiple instances can reference the same definition. See `config/semantic-agents.example.yaml`.

### Semantic resolution

`SemanticIdentityResolver`, injected into OfficeRuntime through `AgentDefinitionRegistry`, owns per-field identity evidence. Authority is native/orchestrator metadata (`source=native`) > project definition > explicit wrapper/API metadata > generic process fallback. Passive transport of AGENT_OFFICE_ID is marked as wrapped evidence, without moving authority selection into the observer. Native callers supply normalized first-class Agent fields; no provider-specific integration or task/prompt NLP is added.

Present, non-empty native fields override definition defaults. Missing/null semantic fields and empty runtime responsibilities mean no new evidence, so partial or legacy registrations retain defaults and existing semantics. Definition responsibilities may be an empty list. Semantic clearing/rebinding through partial registrations is not introduced in this phase. Comparable evidence respects registration recency. Duplicate starts preserve runtime status, tool, activity timestamps, and status provenance; absent optional process/assignment fields cannot erase existing values. Task clearing remains available through TASK_UPDATED. Weaker passive registration cannot overwrite stronger identity.

### office-run

Existing commands and legacy instance-ID derivation remain supported. Optional `--parent`, `--definition`, and repeated `--responsibility` supplement `--name`, `--role`, and `--task`. Metadata is propagated in AGENT_OFFICE_PARENT_ID, AGENT_OFFICE_DEFINITION_ID, AGENT_OFFICE_RESPONSIBILITIES (JSON string array), and existing identity variables. Explicit arguments take precedence over environment defaults. Malformed responsibility environment values are treated as absent. Definition-based launches without `--id` get a definition-prefixed random instance suffix; caller-provided IDs are unchanged. Parentage is explicit and never inferred from the OS process tree.

Definitions are resolved at server registration, not by the wrapper. Therefore project defaults outrank wrapper name/role/responsibilities; native metadata is the authoritative way to override them.

### Frontend and compatibility

Snapshot / agent.started / agent.updated / agent.stopped message shapes are unchanged. The new fields are additive. TypeScript treats them as optional for older servers/fixtures. OfficeScene continues to label characters using the normalized `agent.name`; it has no definition/provider logic and its architecture is unchanged. AgentPanel displays stable role, responsibilities and parent ID when available, alongside separate current task/state/tool and optional definition ID. Old agents remain renderable.

`visualFor(state, deskId)` remains the state-to-current-destination seam. A future role-to-home-zone mapping can be separate; this phase implements no role-based layout or destinations.

## Completed phase: State Fidelity

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

## Implemented arbitration contract

See Decisions 7–10 for the resolved policy choices. API/default evidence ranks between wrapper and tool_process. Runtime stores status evidence internally through `OfficeRuntime.status_evidence(agent_id)`, separately from registration evidence; Agent and WebSocket schemas remain unchanged.

All status-affecting events reject older observation timestamps. Non-native STARTING/THINKING/IDLE can yield to newer fallback activity; other states require equal or higher source authority. TOOL_PROCESS activity stays protected until completion or a stronger accepted event. Rejected events return empty `agent.updated.changes` and do not broadcast or mutate activity metadata.

Duplicate starts enrich identity without resetting activity. Lifecycle stops accept native/wrapper/API/process sources, check status and registration recency, and check an optional expected PID. Wrapper and process observers provide that PID. Missing discovery or access failures do not establish process death.

ToolObserver supplies optional `next_state` / `next_tool` on child start/finish events to describe all remaining live tools. Existing events without these fields retain their previous behavior. TESTING dominates SEARCHING and other tool activity within a scan. Filesystem observation is deferred.
