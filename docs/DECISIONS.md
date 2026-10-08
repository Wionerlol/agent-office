# Agent Office Decisions

## Decision 1: Backend remains the source of runtime truth

**Decision**  
Keep state inference, arbitration, and lifecycle ownership in the backend. The frontend continues to map normalized state to spatial behavior.

**Reason**  
Provider-specific and heuristic evidence must be reconciled once. Duplicating inference in the frontend would make behavior inconsistent and harder to test.

**Rejected alternatives**
- Let the frontend infer status from raw events.
- Send provider-specific Codex events directly into PixiJS.

---

## Decision 2: Add explicit event provenance

**Decision**  
Every normalized AgentEvent should carry a provider-agnostic source/provenance field with a backward-compatible default.

**Reason**  
The runtime currently mixes wrapper events, process scans, child-process tool observations, and timeout heuristics. Without provenance, the runtime cannot distinguish trusted facts from fallback inference.

**Rejected alternatives**
- Keep source only in payload metadata.
- Infer source from event type.
- Let “last writer wins” remain the arbitration model.

---

## Decision 3: Use source precedence plus recency

**Decision**  
Centralize a source-priority policy and combine it with timestamps when accepting status changes.

Initial precedence:
native > wrapper > tool_process > filesystem > git > process > timeout.

**Reason**  
High-confidence evidence should dominate lower-confidence heuristics, while stale evidence should not overwrite newer evidence of comparable authority.

**Rejected alternatives**
- Pure confidence scores distributed across observers.
- Pure timestamp ordering.
- Hard-coded if/else checks in each observer.

---

## Decision 4: office-run owns wrapped-agent identity

**Decision**  
When AGENT_OFFICE_ID exists, the wrapped identity is authoritative. Passive process discovery is fallback detection and must not create a second visible agent for the same wrapped process.

**Reason**  
office-run has explicit identity, repository, role, task, and lifecycle context that generic process scanning cannot reliably reconstruct.

**Rejected alternatives**
- Treat wrapper and passive discovery as equal independent agents.
- Disable passive scanning entirely.

---

## Decision 5: Keep current WebSocket shape compatible

**Decision**  
Preserve snapshot / agent.started / agent.updated / agent.stopped as the frontend protocol.

**Reason**  
The current frontend architecture is already clean and functional. This phase targets state fidelity, not protocol churn.

**Rejected alternatives**
- Replace the protocol with raw event streaming.
- Rebuild the frontend around provider-specific event streams.

---

## Decision 6: No broad UI redesign in this phase

**Decision**  
Do not spend this phase on new rooms, sprites, or layout systems. Minimal diagnostic exposure of provenance is acceptable.

**Reason**  
The current limiting factor is correctness of state interpretation, not visual capability.

**Rejected alternatives**
- Prioritize visual polish before improving runtime fidelity.

---

## Decision 7: API compatibility source sits below wrapper and above tool observation

**Decision**
Use `native > wrapper > api > tool_process > filesystem > git > process > timeout`.
Omitted event sources default to `api`; event timestamps without a timezone are interpreted as UTC.

**Reason**
Existing manually posted state changes remain useful, while API/default evidence cannot displace native or wrapper facts. UTC normalization makes recency comparisons deterministic for old clients.

---

## Decision 8: Keep status evidence internal and distinguish baseline from specific activity

**Decision**
OfficeRuntime keeps source and observation time in an internal `StatusEvidence` record, available through `status_evidence(agent_id)`. Every status-affecting event rejects older timestamps, including stronger sources. Otherwise, source priority governs updates. Equal timestamps are accepted at equal or higher priority, preserving emission order within one observation.

Non-native STARTING, THINKING, and IDLE are baseline states: newer lower-priority evidence may replace them. Native baselines remain explicit facts. Specific activity, WAITING, ERROR, DONE, and OFFLINE retain source protection. TOOL_PROCESS activity remains protected until an accepted completion or stronger event, rather than expiring while a long-running child is alive. After tools finish into THINKING, the existing configured idle timeout can produce IDLE.

Rejected status events return an empty `agent.updated.changes` response, publish no WebSocket message, and change neither tool metadata nor activity timestamps. Accepted activity timestamps never move backwards. Explicit `from` transition checks retain their existing conflict behavior.

**Reason**
Strict priority for all states would permanently prevent tool observations after office-run's initial THINKING event, and permanently prevent idle after tool completion. A fixed freshness lease could incorrectly interrupt long-running tests. Internal evidence preserves existing Agent and WebSocket shapes without requiring frontend changes.

**Rejected alternatives**
- Let timeout displace an active tool after an arbitrary freshness period.
- Expose provider-specific arbitration logic to the frontend.
- Reject every tool observation because the wrapper created the agent.

---

## Decision 9: Separate identity enrichment from activity and make process death explicit

**Decision**
Track registration evidence separately from status evidence. Duplicate starts may enrich identity at equal or higher authority and non-stale registration time, but preserve current activity. Lower-authority discovery cannot replace wrapper identity. Reject mismatched start IDs. Group inherited AGENT_OFFICE_ID processes into one identity using the oldest observed process; preserve existing unwrapped discovery.

A non-stale stop from native, wrapper, API, or process lifecycle can remove an agent regardless of activity priority. Stops also respect registration time and, when supplied, the expected PID. Wrapper and generic lifecycle emitters include their process PID. Duplicate stops are harmless. Passive cleanup may precede the wrapper's final DONE/ERROR update; late status updates retain the existing unknown-agent 404 response, which HttpEventEmitter tolerates. Missing discovery alone is insufficient to stop a still-living PID; adapter failures retain managed identities. Explicitly scanned PIDs that have exited are omitted safely.

**Reason**
A process ending is stronger lifecycle evidence than its previous activity, even though passive activity inference ranks lower. Registration and discovery must not reset ongoing tests. PID guards prevent a delayed stop for an old process from removing the current identity. Permissions or scan failures do not prove process death.

---

## Decision 10: Preserve concurrent tool activity and defer filesystem observation

**Decision**
Tool scans retain per-child start/finish events, with normalized `next_state` and `next_tool` describing the remaining live children. TESTING takes precedence over SEARCHING, followed by other TOOL_RUNNING activity. Only the final child finishing returns to THINKING. Supported agent binaries and Node agent launchers are excluded from tool activity so their prompt arguments cannot masquerade as testing/searching evidence; their actual tool descendants remain observable. Command changes after exec are observed even when PID is unchanged. Access-denied reads retain previously observed children rather than declaring completion.

Do not add a filesystem observer or new timing configuration in this phase. The `filesystem` source exists for future integrations. Keep the frontend unchanged.

**Reason**
A shell or ancillary child finishing must not interrupt an active test/search process. Existing scan and idle settings are sufficient. Filesystem-based CODING remains optional in the handoff and would require separate noise filtering and coalescing work.

---

## Decision 11: Stable semantics extend the existing Agent without replacing runtime facts

**Decision**
Add AgentDefinition (`id`, `name`, optional free-form `role`, and `responsibilities`) separately from runtime instances. Agent gains nullable `definition_id`/`parent_agent_id` and a fresh empty responsibilities list. Existing role is stable responsibility; task is current assignment, status is activity, and current_tool is executable. A parent reference denotes a subagent and may refer to an unobserved parent. Reject self-parent references; do not build or validate an organization graph. Existing EventSource/status arbitration remains unchanged.

**Reason**
A Backend Engineer running pytest remains a Backend Engineer. Definition IDs describe reusable project identities; runtime IDs/PIDs describe individual running instances. Optional fields keep old payloads valid.

**Rejected Alternatives**
- Infer roles or names from current commands, prompts, or tasks.
- Repurpose task/state/tool fields to store identity.
- Require active parent registration or cascade child deletion when a parent exits.

---

## Decision 12: Use the existing project YAML for a repository-scoped definition registry

**Decision**
Support top-level `agents` scoped to the primary project, and per-project `agents` in configured project entries. Match explicit definition_id, otherwise exact instance id, by repository then registered worktree root. Reject duplicate definition IDs within a project; allow reuse across different repositories. An unknown explicit selector uses fallback identity. Load once on server startup. Include a separate example configuration; preserve local office configuration.

**Reason**
This extends the current configuration without a database, new dependency, or implicit cross-project name matching. Multiple runtime instances can share one definition while retaining separate IDs.

**Rejected Alternatives**
- A global registry whose names accidentally apply to every repository.
- Runtime filesystem discovery of definitions or implicit Git/worktree lookups on the event loop.
- Database persistence, hot reload, or fuzzy matching in this phase.

---

## Decision 13: Resolve semantics centrally with per-field authority, apart from activity evidence

**Decision**
OfficeRuntime uses SemanticIdentityResolver. Semantic authority is native/orchestrator (`source=native`) > project definition > wrapper/API compatibility metadata > process fallback. AGENT_OFFICE_ID-tagged passive metadata is marked as wrapped transport evidence; observers never resolve definitions or infer roles. Native normalized fields override defaults individually. API/default events retain a useful explicit-metadata tier alongside wrapper, while callers needing authoritative overrides use source=native. Existing registration source/recency checks remain intact.

Missing/null runtime semantic values and empty runtime responsibilities are absence of new evidence. Duplicate registrations retain stronger semantics and current state/tool/provenance, and omitted optional process/assignment fields cannot erase existing facts. Explicit semantic clear/rebind operations are deferred; TASK_UPDATED still supports changing/clearing the current task. Invalid passive metadata is isolated per process.

**Reason**
Definition names and responsibilities should not be displaced by generic Codex names during discovery or wrapper retries. Native orchestration can provide more precise responsibility and parent metadata. Partial registrations must not remove the process PID being observed or erase defaults.

**Rejected Alternatives**
- Reuse activity source rank as the entire semantic identity policy (definitions must outrank wrapper metadata without changing activity precedence).
- Resolve definitions independently in wrapper, observers, and frontend.
- Let model defaults/nulls silently clear stable metadata.

---

## Decision 14: Propagate explicit relationships and keep presentation/state routing separate

**Decision**
Extend office-run with optional --parent, --definition and repeated --responsibility. Use AGENT_OFFICE_PARENT_ID, AGENT_OFFICE_DEFINITION_ID and JSON-array AGENT_OFFICE_RESPONSIBILITIES, plus existing name/role variables. Arguments override environment defaults. Definition-based launches get a random instance suffix unless --id is supplied; legacy commands retain existing IDs. Parentage is explicit and is not inferred from OS child processes. The server resolves definitions.

Keep OfficeScene unchanged: its existing agent.name label shows enriched identity. AgentPanel adds responsibilities, parent ID, definition, and separate current task/state/tool. New TypeScript fields are optional for old servers and fixtures. Keep visualFor(state, deskId) as the current-destination interface; role-to-home-zone behavior remains separate future work.

**Reason**
One reusable Tester definition can describe several distinct subagents. The current renderer already accepts normalized names, and a small details change is enough to expose semantics without changing room/layout behavior.

**Rejected Alternatives**
- Use definition ID as the unique runtime ID for all instances.
- Treat every OS child executable as an organizational subagent.
- Add role-specific destinations, an organization chart, or a renderer redesign now.


---

## Decision 15: Complete capability discovery before native normalization

**Decision**
Keep Phase 3A in `backend/probe/`, with explicit capture/experiment/observe commands and checked-in evidence. Do not import it from normal startup, change AgentState/EventSource, normalize into AgentEvent, replace SemanticIdentityResolver, or implement CodexNativeAdapter. State Fidelity and Semantic Agent Model remain complete; Phase 3B is unimplemented.

**Reason**
Actual sources differ: CLI 0.159.3 and daemon 0.160.0 expose native input waits, edits and subagents, but not continuous thinking/coding or stable roles in these experiments. Tool hosting outside the TUI subprocess tree makes assumed process coverage unreliable. Evidence must precede adapter/domain decisions.

**Rejected Alternatives**
- Implement a final adapter against assumed/documented events before collecting them.
- Add states/rooms, role inference or filesystem watchers to make uncertain cases appear supported.
- Mark unit fixtures/schema presence as native capability verification.

---

## Decision 16: Prefer structured sources and scope daemon observation to an owned thread

**Decision**
Capture exec JSONL and standalone app-server stdio in controlled runs. For the real DevRouter TUI, connect to the existing local daemon via Unix WebSocket, initialize, verify a selected loaded thread/workspace, then subscribe with thread/resume(excludeTurns=true) without settings/input overrides. Expand scope only through explicit native child identifiers; read child metadata. The observer never answers requests, starts/interrupts turns, loads historical threads or restarts/stops the daemon. Closing it does not imply agent death. The experiment driver alone answers its own fixture question.

**Reason**
The real path preserves bidirectional native events without scraping terminal text. The control socket needs WebSocket framing, and the observed TUI source was vscode, so CLI source labels alone are not sufficient. Pending requests replay on attach; relationships and request IDs must be preserved for future reconciliation.

**Rejected Alternatives**
- Parse arbitrary terminal/ANSI output as the main source.
- Treat app-server proxy as a JSONL socket or assume CLI/daemon versions match.
- Monitor all sessions, auto-answer another client's request, or use OS PPID as subagent ownership.
- Treat selected diagnostic workspace matching as a solved production office-ID/native-thread binding.

---

## Decision 17: Persist a bounded content-denying projection rather than raw runtime logs

**Decision**
Before writing, preserve event discriminators, nested status/item/parent structure, receipt order/timestamps and supplied native timestamp/ordinal. Pseudonymize identifiers consistently. Relativize workspace paths and hide outside paths. Redact text, prompts, tasks, reasoning, arguments, outputs, patches and encrypted content; drop unknown fields including credentials/config/environments/account detail. Retain only bounded executable hints, not shell bodies. Create output exclusively with mode 0600; ignore the entire runtime/probe directory. Publish only reviewed minimal extracts with explicit diagnostic snapshot labels.

**Reason**
Native payloads mix useful runtime structure with sensitive source/prompt/tool/auth content. A deny-by-default field projection protects content before persistence and still allows waiting/parent/lifecycle correlation. app-server receipt time is not an execution timestamp; missing fields and partial observability must remain honest.

**Rejected Alternatives**
- Tee raw stdout/stderr or complete runtime payloads to disk and sanitize afterward.
- Dump environment/config/auth or search unrelated session content.
- Commit giant logs, replay free text into the frontend, or discard event structure so important null/relationship facts disappear.


---

## Decision 18: Bind Office identity to native thread explicitly and retain session ownership

**Decision**
Use a runtime-local one-to-one NativeThreadBinding registry and explicit bind API. Require an existing Codex Office ID, a supplied native thread ID, already-loaded metadata and matching repository/worktree. Repository is validation only. Matching retries are idempotent; conflicts fail. Store the Office generation, native parent/root identity and completed-child tombstones, bounded to 1,024 records without silent eviction. Reconnect preserves bindings; restart requires a new handshake. Ordinary DevRouter does not supply a reliable native UUID, so v1 requires the explicit API rather than pretending automatic binding exists.

**Reason**
Several agents can share a repository. Native identity and lifetime must not jump based on CWD or inherited process relationships. A small explicit handshake fits the installed daemon and avoids modifying external DevRouter or scraping its terminal.

**Rejected Alternatives**
- Choose the only/most recent thread for a repository or scan terminal UUID text.
- Equate Office IDs, native session IDs and OS PIDs.
- Evict/rebind identities silently or add database persistence.

---

## Decision 19: Bound idempotence and reconstruct structural activity on reconnect

**Decision**
Deduplicate thread/turn/item/request/fact/phase/child keys with bounded LRUs. Correlate resolution to the request turn/item; maintain completed-item and retired-turn tombstones. Replayed pending requests may reconstruct lost waiting without duplicate display updates. Status notifications deduplicate derived values. Initial subscription reconciles the latest turn; reconnect catches up to its checkpoint within 32 turns and 800 items/turn. Project history into structural facts, not stored content. Completed unbound historical children are not newly displayed. Overflow/unavailable structure releases native activity and degrades to fallbacks.

**Reason**
Phase 3A observed pending-request replay. Event dedup alone cannot restore missed completion or current waiting after disconnect, while unbounded history and tombstones would turn this into a general event-sourcing system.

**Rejected Alternatives**
- Rely on last-writer-wins or reconnect as fresh agent registration.
- Cache every status value forever, suppressing later legitimate idle/active changes.
- Persist raw logs/database state or hydrate arbitrary/all user threads.

---

## Decision 20: Keep WAITING and add explicit waiting context

**Decision**
Add waiting_reason and waiting_on_agent_id with None defaults. Confirmed user request/flag produces WAITING/user_input; idle is separate and cannot cancel a pending request. Resolution/turn termination clears context. Only a native wait naming exactly one mapped, live immediate child produces child_agent plus its Office ID. Empty/multiple recipients and merely having active children do not establish waiting-on-child. AgentPanel displays normalized context; OfficeScene stays unchanged.

**Reason**
The developer needs to distinguish a suspended input decision from a completed/idle turn. Phase 3A did not establish universal child-wait flags, so uncertainty must remain explicit.

**Rejected Alternatives**
- Add many top-level waiting states or collapse input waiting into idle.
- Assume all parent/child relationships imply a blocked parent.
- Let the monitoring connection answer or approve requests.

---

## Decision 21: Generated native nicknames are fallback names, not organizational definitions

**Decision**
Store native_nickname and mark the incoming name generated; SemanticIdentityResolver assigns generated names fallback authority. Non-generated authoritative native semantic fields retain their existing highest tier. A bind request may explicitly select a project child_definition_id; do not infer it from role/task/prompt/tool text. Null native roles never erase project role/responsibilities. Native child identity uses a stable thread hash and native parent evidence, independent of PID.

**Reason**
Actual names such as Averroes/Dirac/Galileo do not describe stable Tester responsibilities, and actual native roles were null. Project semantics must remain useful without pretending generated names are authoritative organizational assignments.

**Rejected Alternatives**
- Let generated nickname automatically replace Tester or rename a child Reviewer from its prompt.
- Bypass the resolver, remove definitions, or use OS subprocesses as subagents.
- Fabricate child result text or treat activity completion alone as proof of success.

---

## Decision 22: Aggregate native activities centrally and preserve independent lifecycle

**Decision**
Use one per-thread activity policy: explicit terminal outcome; user input; one deterministic child wait; testing; searching; file change; generic command; confirmed idle or released baseline. Reasoning is diagnostic-only in v1. Command labels reuse existing classification, not native state names. Completion removes only its own activity; nonzero command exit is metadata, not whole-agent ERROR. Only successful file completion adds scoped paths. Successful child turn becomes DONE, failure ERROR, then configurable grace/stop; fresh confirmed child turns can retain/reopen the same identity. Known children continue after parent removal; replay never recreates a completed child without new active-turn evidence.

**Reason**
Concurrent command/file completion must not interrupt tests. Native reasoning coverage and child result delivery are incomplete. Lifecycle independence preserves real child work without a complex organizational tree.

**Rejected Alternatives**
- Reset THINKING after every individual completion or mark the whole agent ERROR for every failed command.
- Treat reasoning items as complete model-phase coverage or add filesystem CODING/NLP.
- Immediately remove children, revive historical completed agents, or cascade child death from parent exit.

---

## Decision 23: Read-only exact-version consumer releases evidence into existing fallback arbitration

**Decision**
Use a separate production Unix WebSocket consumer with exact reviewed app-server profiles 0.159.3/0.160.0/0.160.1 and discovery/initialize version agreement. Permit only metadata reads, structural pagination and loaded-thread resume without configuration overrides. Unknown versions fail closed. Declare the already-transitive WebSocket library as a direct dependency without a locked-version upgrade. Production never imports the probe or persists raw payloads.

An explicit native release supplements Decision 8: when no specific native activity remains or the consumer disconnects, native baseline authority may yield without falsely stopping the agent. OfficeRuntime retains private ToolObserver aggregate facts even when their display is rejected. Release restores a still-active fallback with its original source tier; finished tools are not revived. A newer tool snapshot delayed across that handoff reconciles at its timestamp floor, without rewinding status/active time. This narrow reconciliation does not permit older ordinary state events to overwrite newer evidence. Terminal states retain protection, and repeated outage retries do not refresh idle time. Legacy native events without release retain the original policy.

**Reason**
An unavailable native connection must not leave WAITING/TESTING locked forever, and removing native activity must not lose an independently running fallback test. Experimental protocol upgrades need evidence and an explicit compatibility boundary. The consumer must enrich OfficeRuntime rather than bypass it or control the user's TUI.

**Rejected Alternatives**
- Leave stale native authority frozen, globally weaken native priority, or change every observer's arbitration.
- Silently parse future versions, restart the daemon, auto-answer requests, or change TUI configuration.
- Store raw prompts/output/patches or expose provider-specific frontend events.

---

## Decision 24: Explicit launch identity enables a background binding handshake

**Decision**
After wrapper registration, office-run can bind using a literal `codex resume UUID`, `--native-thread UUID`, or `AGENT_OFFICE_NATIVE_THREAD_ID`. Literal resume identity and supplied identity must agree. Pass the exact Office started_at generation to the bind API, retry the same handshake for at most 30 seconds in the background, and cancel on wrapper exit. Disabled native integration does nothing. Consume the wrapper's leading `--` delimiter so the installed DevRouter command launches the intended Codex subcommand. A fresh TUI, picker, session name, --last or ambiguous arguments remain unbound; use `agent-office native bind AGENT UUID` when an explicit operator step is needed.

**Reason**
Installed CLI 0.160.0 / daemon 0.161.0 and DevRouter were inspected. Thread metadata exposes originator/session/source classifications, not an Office-owned launch nonce. Environment identity does not become a structured thread field. Consumer-owned thread creation or injected TUI configuration would change the read-only boundary. A launcher-known resume UUID is genuine explicit evidence and works through both paths without manual HTTP.

**Rejected Alternatives**
- Newest/only thread, repository, PID proximity, terminal scraping or guessed nonce metadata.
- Claim fresh-session automatic discovery without native evidence.
- Block or fail ordinary Codex execution when Agent Office is unavailable.

---

## Decision 25: Native failures follow logical thread ownership

**Decision**
Retain the existing connection per root with its confirmed children; do not add a socket per child. Catch selected-thread parsing, hydration, subscription/read rejection, binding and catch-up failures at the affected thread. Release only that thread's activity evidence, preserve siblings/root, and retry bounded structural reconstruction on the same connection. Failed child discovery retains a bounded structural delegation fact without manufacturing a child. Root read failure also leaves already-known children observable. Malformed transport envelopes, socket loss, request timeout and unsupported handshake are connection-level boundaries for that root's connection; unrelated roots continue independently. Child CLI reconnect schedules only child reconstruction. Backlog limits are 128 queued facts per thread, 512 per root connection, and at most 1,024 pending child retries.

**Reason**
A rejected child read does not prove transport loss or agent death. Distinguishing these boundaries prevents a child from freezing the whole office while preserving the v1 source-release, recency, terminal and semantic contracts. Bounded retries avoid uncontrolled memory/history growth.

**Rejected Alternatives**
- Whole-provider degradation after every child exception.
- A WebSocket per child or automatic daemon restart.
- Broadly weakening provenance to make fallback appear usable.

---

## Decision 26: Reviewed capability profiles gate experimental protocols

**Decision**
Centralize exact versions, schema family, read RPCs, fact methods, item types and thread/turn discriminators in ProtocolProfile. The reviewed paginated profile covers 0.159.3, 0.160.0, 0.160.1 and newly reviewed 0.161.0. Unknown versions and initialize/discovery disagreement fail closed. Compatibility validation uses only discovery/initialize and, when explicitly selected, loaded-thread reads/subscription and paginated structural shape checks; it never starts turns, answers requests or overrides configuration. Unknown versions report review_required without opening a production transport.

**Reason**
The locally installed daemon upgraded to 0.161.0 independently of this work. Its generated Thread/ThreadStatus/Turn/ThreadItem/ThreadItemEntry/SubAgentActivityKind definitions match reviewed 0.160.1 schemas. Actual read-only handshake/read RPC and controlled TUI/DevRouter smoke validate the consumed subset. This supports a deliberate exact addition, not an open-ended version range or universal schema guarantee.

**Rejected Alternatives**
- Lexicographic/minimum-version gates, silently accepting future schemas or model calls as compatibility probes.
- Scattered per-event version checks.
- Changing/downgrading the shared daemon to hide compatibility failures.

---

## Decision 27: Local integration health stays separate from AgentState

**Decision**
GET /api/native/codex reports provider, discovered version, protocol status, aggregate integration health, per-binding health/fallback/category/scope/type, unbound Office IDs, bounded unbound-child failures and the latest categorical bind failure. Health is disabled/unbound/connecting/connected/reconnecting/degraded/unsupported/unavailable/inactive; it is not AgentState. CLI status/bind/reconnect uses loopback HTTP only; validate talks to the existing local daemon read-only. Native IDs remain developer control-plane information and are not added to Agent/frontend models. Error text, prompts, questions, reasoning, arguments, output and patches never enter diagnostics. Keep the expected server default 127.0.0.1; no authentication system or normal UI redesign is introduced.

**Reason**
Operators need to distinguish observer failure from agent activity, see whether fallback is in use and inspect exact binding ownership. Backend diagnostics and a small CLI provide this without provider logic in OfficeScene or exposing native content in normal UI.

**Rejected Alternatives**
- New AgentState values for connection health.
- Raw exception/native content in API errors, permanent probe logging or UUID labels on characters.
- New LAN/public native control surfaces.

---

## Decision 28: Fresh-session correlation stops at the current runtime boundary

**Decision**
Treat fresh-session automatic binding as an upstream/current-runtime limitation. Do not implement Phase 3B v1.2 or heuristics. Keep literal resume UUID, explicit argument/environment and operator native bind paths intact. Require a future demonstrated launcher-owned structured token or an explicitly approved creation/attach contract before revisiting automatic correlation. Recommend Phase 4 as a separate next task.

**Reason**
The installed 0.160.0 fresh TUI was blocked by shared feature incompatibility; matching installed 0.161.0 CLI/daemon experiments produced five real fresh threads through direct office-run and actual DevRouter. Same-repository concurrent pairs exposed different native IDs but identical vscode/codex-tui classifications, with no controlled correlation/originator-override nonce. Observer reconnect preserved native IDs without revealing Office ownership. Installed DevRouter also reuses a repository-derived Office ID across independent homes. See runtime-probe/FRESH_SESSION_CORRELATION.md for scoped evidence, failed candidates and limits; no configuration/daemon restart or injected turn was used to force success.

**Rejected Alternatives**
- Newest/only thread, repository/PID/timing/name/prompt guesses or terminal scraping as automatic identity.
- Treat generic source/session IDs or schema-only metadata possibilities as confirmed causal ownership.
- Become a Codex turn controller, inject a first turn, install hooks/configuration or restart the shared daemon to solve observation identity.
- Keep expanding runtime recovery infrastructure after this focused negative result.


---

## Decision 29: Home Zone and Current Destination are separate visual concepts

**Decision**
A pure frontend planner exposes role home separately from activity destination. OfficeScene consumes it incrementally; backend state and native adapters do not acquire layout concepts.

**Reason**
Testers and engineers thinking need distinct spatial identity, while Backend agents testing must visit Test Lab. Existing normalized facts are sufficient.

**Rejected Alternatives**
- Put rooms in backend state; scatter role/state checks through rendering; infer runtime state from animation.


---

## Decision 30: Spatial precedence protects lifecycle and attention

**Decision**
Use lifecycle, explicit user attention, deterministic child coordination, active work, role home, then generic fallback. DONE celebrates immediately in place during existing grace; ERROR retains visible existing behavior.

**Reason**
Attention must remain recognizable regardless of role. Work overrides home without erasing it, and short-lived children must signal completion before cleanup.

**Rejected Alternatives**
- Let role override testing/searching; infer waiting from active children; extend backend grace solely for animation.


---

## Decision 31: Role homes use exact aliases and safe fallback

**Decision**
Keep trimmed lowercase exact aliases in one mapping: tester/testing/qa → Test Lab; research/researcher → Library; reviewer/code_review/review → Review; engineering/lead aliases and unknown roles → assigned desks.

**Reason**
Identity already supplies organizational semantics. An explicit mapping is predictable and can later become configurable without NLP.

**Rejected Alternatives**
- Substring, task, tool or prompt role inference; role editor/configurable room system in Phase 4A.


---

## Decision 32: Attention and coordination are compact spatial cues

**Decision**
WAITING/user_input visits NEEDS YOU with a restrained question marker. WAITING/child_agent uses shared lounge coordination only with a nonempty, non-self child ID. Add a modest Review Area, retaining names/status and content-free accessible summaries.

**Reason**
Space should reveal user attention and deterministic child waiting without opening details. Compact markers remain readable with several waiting agents, without native question content.

**Rejected Alternatives**
- Chat/reasoning bubbles; organization graphs/permanent lines; treat generic waiting as input; full office redesign.


---

## Decision 33: Stable reservations reuse existing movement machinery

**Decision**
Reserve seats per visible ID/zone, prune released ownership, share lounge/coordination seats and grow dense grids only at capacity thresholds. Keep routing/separation/z ordering; use fixed movement steps and reroute stalled or displaced actors. Simulation uses the same projection.

**Reason**
Shared functional zones need distinct targets without unrelated reshuffling. Controlled smoke exposed doorway congestion and displaced seats; targeted recovery preserves existing pathing and tolerates uneven frames.

**Rejected Alternatives**
- Rebuild Pixi or randomize seats on updates; retain departed IDs forever; add a physics/layout engine; guarantee unlimited readable density.


---

## Decision 34: Persistent truth and transient interaction cues are separate

**Decision**
Keep persistent coordination/error/attention projections separate from content-free frontend InteractionCue records. SpatialBehavior continues to own destinations; cues do not change movement or backend truth.

**Reason**
Current waits last while true; delegation/completion represent short lifecycle edges. Mixing them creates permanent or stale relationship visuals.

**Rejected Alternatives**
- Put interaction fields/events in backend Agent models; overload recentEvents; turn parentage into permanent visuals.


---

## Decision 35: Only normalized incremental lifecycle edges generate transient cues

**Decision**
Generate delegation for a new child start with known parent, handoff on non-DONE → DONE, and local blocked emphasis on non-ERROR → ERROR. Snapshots clear transient state and seed identities, without historical animations. Live and simulation share the same normalized message handler.

**Reason**
Reconnect is current truth, not an event replay UI. Status edges and lifecycle identity make repeated normalized updates idempotent.

**Rejected Alternatives**
- Animate snapshot children/completions; infer teams/delegation from task strings, processes or raw provider events; propagate child ERROR to parent.


---

## Decision 36: Active child waiting alone permits a persistent coordination link

**Decision**
Draw a quiet connector only for explicit WAITING/child_agent with a currently rendered non-self target. Resolve live endpoints each frame; filtered/missing targets keep only local spatial cues. Preserve NEEDS YOU priority.

**Reason**
The office should communicate current collaboration without becoming an organization graph or changing normalized relationships based on filtering.

**Rejected Alternatives**
- Permanent parent-child lines; fabricated endpoints; extra routing or parent state changes for delegation/handoff.


---

## Decision 37: Bounded cues and centralized maintenance define replay and expiry limits

**Decision**
Cap cues at 48 and remembered start generations at 128. Use fixed 3s delegation/handoff and 4s blocked TTLs, current generation/status-edge checks and one App-owned 250ms sweep. Keep existing 5s offline grace in this maintenance owner; duplicate stops never extend it and a new registration cancels stale cleanup. Pause stops simulation changes, not TTL expiry.

**Reason**
Short cues need deterministic cleanup, bounded resources and reconnect safety without a history system or timer per visual primitive.

**Rejected Alternatives**
- Unbounded event/dedup history; random durations; one timer per cue; leak stop timers on unmount; indefinitely replay retired starts beyond the bounded window.


---

## Decision 38: Interaction rendering is extracted and uses compact readable symbols

**Decision**
Keep a dedicated content-free InteractionLayer with reused Graphics/keyed badges and live endpoint projection. Quiet lines stay below characters; short directional pulses cross foreground furniture. Use →/↔/✓/! with a small text legend and accessible relationships. ERROR retains ! after entry emphasis expires; user attention suppresses competing packets.

**Reason**
Timed real browser review found that travelling text was hidden by desks and multiple blocked labels overlapped. Compact symbols improve legibility without a redesign or private text.

**Rejected Alternatives**
- Add drawing/state-machine logic to the movement loop; rebuild Pixi on updates; heavy animation dependencies; raw question/error text or color-only failure cues.
