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
