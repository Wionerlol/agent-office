# Agent Office Implementation Spec

## Phase state and diagnostic contract

| Phase | State |
| --- | --- |
| 1 State Fidelity | COMPLETE |
| 2 Semantic Agent Model | COMPLETE |
| 3A Native Runtime Capability Probe | COMPLETE |
| 3B Native Adapter v1 | COMPLETE |
| 3B v1.1 Native Hardening | COMPLETE |
| Fresh-session correlation | COMPLETE: current-runtime limitation |
| 4A Role-Aware Spatial Team Behavior | COMPLETE |
| 4B Team Interaction & Coordination Cues | COMPLETE |
| 4C | NOT YET IMPLEMENTED |

## Native Runtime v1 contract

The normative Phase 3B contract is [NATIVE_RUNTIME.md](NATIVE_RUNTIME.md), with Decisions 18–23. `backend/native/codex/` owns versioned read-only transport, explicit bindings and bounded structural snapshot reconciliation; `backend/adapters/codex_native.py` normalizes facts into OfficeRuntime. Production does not import the probe, persist raw payloads, or change OfficeScene routing.

Agent adds nullable `waiting_reason` and `waiting_on_agent_id`. Native user input produces WAITING/user_input, independently of idle. Only one deterministic mapped immediate child permits WAITING/child_agent. State updates apply context/tool changes atomically through provenance arbitration and clear waiting context on leaving WAITING. No top-level states or WebSocket message types change.

Native nickname is metadata plus a generated fallback name; SemanticIdentityResolver gives that name fallback authority, preserving stronger definitions and authoritative non-generated native identity. Null roles remain absent evidence. Native child identity is stable per thread, with explicit parent, successful DONE/failed ERROR, and terminal grace before cleanup.

Native activity aggregates waits, commands and file changes centrally. Specific native evidence outranks fallback; a baseline after completion or disconnect explicitly releases evidence. OfficeRuntime remembers the private latest ToolObserver aggregate without changing rejected-event behavior; it restores a still-active fallback with its source tier. Delayed newer tool snapshots may reconcile a restored handoff at its timestamp floor without rewinding recency; ordinary stale status events still fail. Legacy native evidence without release retains its historical protection.

Opt-in configuration defaults disabled. Explicit POST `/api/native/codex/bind` requires Office ID plus native UUID; workspace only validates. GET `/api/native/codex` reports scoped bindings/version/failure class; POST `/api/native/codex/reconnect/{agent_id}` closes/reconnects only observation. Exact compatible daemon profiles: 0.159.3, 0.160.0, 0.160.1, with discovery/initialize agreement. Unknown versions and source loss safely fall back; no automatic DevRouter UUID discovery is claimed.

The Phase 3A diagnostic contract below remains intact and historical: its exclusions apply to the probe, while the separate Phase 3B adapter is now explicitly authorized.

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

## Phase 3B v1.1 operational contract

Preserve Decisions 1–23 and the native normalization architecture. Decisions 24–27 define explicit launch binding, failure boundaries, reviewed protocol profiles and developer health. office-run uses literal resume UUID or explicitly supplied --native-thread / AGENT_OFFICE_NATIVE_THREAD_ID after registration; it never searches by repository, PID, newest/only session, prompt or terminal. Generation-aware background retries are bounded and cancel on exit. DevRouter's wrapper delimiter is consumed before forwarding Codex arguments. Ambiguous/fresh/picker launches remain unbound.

`agent-office native status|bind|reconnect|validate` provides local operator workflows. Bind adds optional expected_generation to the existing API; new clients always supply it. GET /api/native/codex adds protocol/health and per-binding fallback/failure category/scope/type. Thread IDs stay in developer diagnostics, not frontend models. Keep loopback as the expected server default.

Reviewed profiles centralize version/RPC/fact/item/discriminator assumptions; exact 0.161.0 joins previously reviewed versions after local schema and runtime review. Unknown versions fail closed; validation never starts turns or answers native requests. Selected-thread read/parsing/hydration/backlog errors degrade and release only that thread; typed connection loss/timeout/unsupported handshake affects its root connection. Existing one-root-plus-children multiplexing is retained, with bounded retries and no socket per child. See NATIVE_RUNTIME.md for limits, health contract and real evidence.


## Phase 4A spatial interpretation contract

Runtime truth stays in the backend. The pure `spatialBehaviorFor` planner in `frontend/src/office/visual.ts` consumes role, status and normalized waiting context, returning home, destination, animation, attention and terminal hold policy. OfficeScene applies it incrementally without rebuilding Pixi or parsing native events. Backend models, identity, provenance and native integration are unchanged.

Spatial precedence:

1. Lifecycle: STARTING entrance; OFFLINE exit; DONE immediate celebration at existing position (home for a new terminal snapshot); ERROR existing visible desk error behavior.
2. WAITING/user_input: User Attention with compact `?` and NEEDS YOU title; no question content.
3. WAITING/child_agent with a nonempty, non-self waiting_on_agent_id: shared lounge coordination and Child wait marker. Parentage alone never implies waiting.
4. Active work: TESTING Test Lab; SEARCHING Library; TOOL_RUNNING Tool Lab; CODING assigned engineering desk.
5. THINKING/IDLE: role home, retaining contemplation/relaxed animation.
6. Generic WAITING: lounge; absent/unknown roles: assigned desk home.

Exact aliases after trim/lowercase only:

| Roles | Home |
| --- | --- |
| tester, testing, qa | Test Lab |
| research, researcher | Library |
| reviewer, code_review, review | Review Area |
| backend, backend_engineer, frontend, frontend_engineer, lead, leader, coordinator | Assigned desk |
| absent or any other string | Assigned desk |

Review and User Attention use existing unused left-side space without new walls. Coordination shares the lounge. No permanent parent-child lines or organization layout is added.

`StableZoneSlots` reserves seats per visible ID and canonical zone, sharing lounge/coordination allocation. Existing reservations survive unrelated updates/departures. Returning agents claim a free seat without reshuffling peers. Comfortable capacities: Test Lab 4, Library 3, Review 2, User Attention 3, Lounge 2, Tool Lab 3. Beyond capacity, the existing scaled grid grows at thresholds and retains its high-water capacity until the zone empties. Dense grids may shrink sprites/hide labels. Memory is bounded by visible agents and occupied zones; departure/teardown releases reservations.

Movement retains walkable grid/A*, separation and y ordering. Fixed movement steps tolerate variable frame cadence; only stalled routes and displaced seated actors are rerouted. Destination changes occur only when plan/seat changes. DONE immediately stops walking, using unchanged backend terminal timing.

Simulation uses normalized roles, parent IDs and waiting context through the same scene path. Pause/Resume freezes demo transitions for inspection. Semantic names remain authoritative; no native UUID, prompt, reasoning or tool output is exposed.


## Phase 4B interaction contract

`models/interaction.ts` defines frontend-local InteractionCue (`id`, `kind`, `sourceAgentId`, optional `targetAgentId`, `createdAt`, `expiresAt`). It is separate from AgentState, backend AgentEvent and SpatialBehavior. Existing ServerMessage shapes remain unchanged. Zustand holds `interactionCues` independently of `recentEvents`.

The shared `applyServerMessage` → store `receiveMessage` path atomically applies normalized truth and emits cues:

- A genuinely new `agent.started` lifecycle with a known non-offline, non-self parent creates parent → child delegation. Current Agent generation plus bounded `(id, started_at)` start keys prevent duplicate registration animation.
- Incremental previous status != DONE → DONE with a known parent creates child → parent handoff. DONE → DONE creates nothing.
- Incremental previous status != ERROR → ERROR creates local blocked emphasis. ERROR → ERROR never refreshes it; parent status is untouched.
- Snapshot replaces current truth and clears transients, seeding current start identities without replaying historical delegation/completion. It reconstructs persistent waits and ERROR indicators only.
- Stops/removal immediately discard dependent cues. Re-registering an ID with a new generation discards old cues and cancels old offline cleanup. No payload/task/output/native text is copied into a cue.

Persistent coordination requires WAITING/child_agent plus a non-self target present in the rendered, non-offline subset. Parentage alone never creates an edge. Clearing waiting immediately removes the connector on the next frame. Missing/filtered targets leave the Phase 4A local coordination marker intact without ghost lines or backend relationship changes.

Central policy: delegation 3s, handoff 3s, blocked emphasis 4s; at most 48 cues and 128 remembered start keys. Current registered identities still suppress duplicate starts after key eviction; retired lifecycle dedup is bounded, not an infinite history guarantee. One App-owned 250ms maintenance interval removes expired cues and handles existing 5s offline grace. Duplicate stops do not extend that grace. Pause stops scripted simulation changes, while ephemeral TTL cleanup continues. Unmount clears the interval; renderer also refuses expired cues, including background-tab delays.

`office/interactions.ts` owns pure frame projection and a dedicated Pixi InteractionLayer. Each frame resolves live character positions/scales; it never alters destinations, routing, collisions, status or identity. One reused Graphics draws connector segments/rings, while keyed glyph primitives are retained until expiry/visibility loss. Connectors and quiet coordination glyphs remain below characters/labels; compact travelling pulses cross foreground furniture, and local error markers remain readable above it. Scene teardown destroys both layer containers and their children. Persistent objects scale only with visible waits/errors; transient objects are bounded by the cue cap.

Visual vocabulary: `→` travels parent → child and points along its trajectory; `✓` returns child → parent; `↔` denotes active child waiting; `!` persists for ERROR, with a brief ring on entry. A compact text legend and content-free accessible scene description explain these symbols. WAITING/user_input retains NEEDS YOU/`?`; transients touching a user-attention agent are suppressed and an explicit coordination link targeting one is quieter. No private question/error text is shown.

Demo simulation uses the same normalized start/update/stop path for a Test Partner cycle: spawn → Lead wait → child DONE → Lead resumes/child stops → Reviewer error/recovery. The user-input waiter remains visible. Pause/resume preserves the next script step and cancels scheduled changes cleanly. No new backend events or domain fields are introduced.
