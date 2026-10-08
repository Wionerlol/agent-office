# Agent Office Acceptance Criteria

Current state: Phases 1–3B v1.1 and fresh-session investigation COMPLETE; Phase 4A COMPLETE; Phase 4B COMPLETE; Phase 4C NOT YET IMPLEMENTED. Earlier phase sections below retain their historical evidence.

## Fresh-session deterministic correlation investigation — COMPLETE

- Investigation-only; no production binding/domain/frontend changes or Phase 3B v1.2. Existing explicit UUID paths, generation checks, replay, native activity and fallback behavior remain unchanged.
- Current CLI/help/generated schemas and installed DevRouter launch code inspected. [The report](runtime-probe/FRESH_SESSION_CORRELATION.md) includes all candidates, classifications, minimal sanitized samples and reproduction boundaries.
- Real matching CLI/daemon 0.161.0 exercised fresh direct launch, two concurrent direct launches and two actual concurrent DevRouter launches in the same repository. Five native thread/started events were collected before any model turn. No controlled nonce was present; generic source/originator did not distinguish ownership. No prohibited identity heuristic was used.
- Observer reconnect read all five running threads without recovering Office ownership. Final native diagnostics remained unbound with zero bindings. DevRouter's duplicate repository-derived Office ID is an explicit external limitation, not falsely reported as two independent Office registrations.
- PATH CLI 0.160.0 fresh-start feature incompatibility and an initial folder-trust/setup run are excluded from successful evidence. Matching installed CLI selection did not restart/reconfigure the shared daemon. No turns, hooks, controller/proxy or approval automation were added.
- Outcome: **UPSTREAM / RUNTIME LIMITATION**. Preserve explicit CLI bind; recommend Phase 4 separately. Do not continue indefinite recovery work to force automatic discovery.

Verification on 2026-10-08: `uv run pytest -q` **210 passed / 2 existing deprecation warnings**; `uv run ruff check backend main.py` passed; frontend `npm test -- --reporter=dot` **29 passed / 12 files**, `npm run lint` and `npm run build` passed. No tracked diagnostic/correlation code was added, so no synthetic tests are represented as fresh runtime evidence. Required `Backend` / `Frontend` checks and `git diff --check` remain delivery gates; exact hosted results belong to the final PR commit.

## Phase 3B v1.1 Native Integration Hardening — COMPLETE

- Explicit literal-resume or supplied-UUID launch binding works without a user HTTP request; ambiguous/fresh/picker/name/--last cases remain unbound. Background retries preserve the same Office generation and cancel on exit; conflicts fail closed. No CWD/process/terminal guessing.
- Direct office-run and the actual installed DevRouter path both exercise literal-resume handshakes. Fresh-session automatic UUID discovery is **not supported**; one explicit native bind CLI command is the remaining operator workflow once a UUID is known.
- Selected-thread parse/read/hydration/reconciliation/backlog failures release only that thread and reconstruct on the existing root socket. Shared connection loss/timeout or unsupported protocol releases the root connection's scope; unrelated roots stay native. Child reconnect does not close its root socket.
- Exact ProtocolProfile centralizes reviewed version/RPC/fact/item/discriminator assumptions. Unknown/mismatched versions fail closed. The independently upgraded daemon 0.161.0 is added only after generated schema comparison, read-only validation and real owned smoke.
- Local CLI status/bind/reconnect/validate and GET diagnostics report protocol, health, binding ownership, fallback, failure category/scope/type and bounded unbound-child failures without native content. Integration health stays separate from AgentState; frontend and OfficeScene are unchanged.
- All v1 native activity, waiting, semantic identity, child lifecycle, replay, terminal protection and fallback regressions remain; OfficeRuntime provenance policy is unchanged. No Phase 4 work, database, filesystem observer, NLP or native answering/control is added.

### Local deterministic verification (2026-10-08 Asia/Singapore)

- `uv run pytest -q`: **210 passed**, including **32 new hardening contracts** and all 178 prior regressions; two existing Starlette/httpx/anyio deprecation warnings.
- `uv run ruff check backend main.py`: passed.
- `cd frontend && npm test -- --reporter=dot`: **29 passed / 12 files**.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.
- Required hosted checks: **Backend** and **Frontend** must pass on the final PR commit; their authoritative results are recorded in the PR/check run rather than inferred from local execution. All deterministic cases run in CI; the existing ripgrep installation supports credential-free process regressions. Real Codex/DevRouter smoke is excluded from hosted CI.

Contracts cover explicit launch identity/ambiguity/conflicts, DevRouter delimiter/environment, bounded handshake retry, generation swap during native read and simultaneous binding races, child/root/live-consumer isolation and recovery, fallback authority, child-only reconnect, protocol profiles/unknown versions, malformed selected facts, safe validation failures and disabled/unbound/degraded health. A v1 unknown-version fixture deliberately moves from 0.161.0 to 99.0.0 because 0.161.0 is now explicitly reviewed; its no-transport assertion remains intact. No assertion is skipped or weakened.

### Real owned runtime evidence

Final disposable run uses CLI **0.160.0**, shared daemon **0.161.0**, two owned native roots in the **same** workspace, a real direct office-run TUI and the actual installed DevRouter CLI → tmux → office-run → TUI. A separate fixture owner obtains explicit UUIDs from its own structured creation and initiates its own turns/answers. Neither the production observer nor the wrapper answers/approves/starts/interrupts turns or changes daemon/TUI settings.

The final run exits 0 with **44 normalized structural messages** and verifies:

1. Direct explicit resume automatically binds the registered Office ID; no user bind HTTP call.
2. Actual DevRouter explicit resume automatically binds its different Office ID to its different root UUID despite the shared workspace.
3. CLI status and selected-thread validate succeed with discovery, initialize, read, no-override subscribe, turns/list and items/list checks.
4. Actual apply_patch 41→42, rg and pytest produce CODING/SEARCHING/TESTING; modified file checked independently.
5. Plan requestUserInput produces WAITING/user_input; pending reconnect reconstructs it, fixture-owner resolution clears it.
6. Real native child **Kepler** displays project-defined **Tester**/tester/Run tests with correct parent. Exactly one child appears across reconnect; successful completion displays DONE before grace cleanup.
7. Injected child metadata-read failure degrades that child while its parent and the independent DevRouter root stay connected; recovery/reconnect preserves identity. This is labeled fault injection, not a claimed spontaneous provider failure.
8. Closing the direct root consumer's actual observation connection leaves the DevRouter root usable; its subsequent real rg produces native SEARCHING. Controlled normalized fallback input restores direct-root TESTING; this input is a contract fixture, not additional process/native capability proof.
9. CLI reconnect restores direct-root connected status without duplicate children. HTTP frontend serving remains available; unchanged frontend behavior is covered by its regressions and prior v1 browser evidence, not a new v1.1 visual claim.

Two controlled hardening runs pass; full logs/helpers/manifests remain ignored. The small fixture-driver implementation errors and one unsupported-version fixture update were corrected before final verification; passing results correspond to the reviewed final implementation. Older profiles retain historical Phase 3A/v1 evidence; this new live smoke covers 0.161.0 only. Fresh-session nonce correlation, universal THINKING/approval waits/child waits, arbitrary native roles, huge catch-up and indefinite child reuse remain unsupported/partial. See NATIVE_RUNTIME.md and Decisions 24–27.

Phase 1 COMPLETE; Phase 2 COMPLETE; Phase 3A COMPLETE; Phase 3B v1 COMPLETE; Phase 3B v1.1 COMPLETE. Phase 4 NOT YET IMPLEMENTED.

## Phase 3B Native Runtime Adapter v1 — COMPLETE

- Explicit registered Office ID/native UUID binding, loaded-thread workspace validation, conflict/generation rejection, sticky reconnect and child binding are covered. CWD-only identity is rejected.
- Production consumes only version-gated local structured sources through CodexNativeAdapter → OfficeRuntime. It never answers, approves, starts/interrupts turns, changes TUI settings, restarts the daemon or imports the probe. Disabled/unavailable/unsupported native integration leaves existing behavior operational.
- Bounded replay keys, request correlation, retired turns and completed items protect idempotence. Snapshot reconstruction restores live activity; terminal cleanup retains binding tombstones.
- Native input waiting yields WAITING/user_input; idle cannot cancel a pending request, and resolution clears context. Single deterministic child wait is supported; empty/multiple recipients remain partial.
- Confirmed native children have stable Office identity, native parent relationship, project semantics stronger than nickname/null role, independent lifecycle, terminal presentation and cleanup.
- Native command classification and file activity aggregate concurrent work; a file completion cannot interrupt native testing or lose a still-active fallback test. Nonzero command exit is preserved without whole-agent ERROR. Failed patch does not claim a changed file.
- Waiting fields are additive in HTTP/WebSocket snapshots/updates and visible in AgentPanel. OfficeScene remains unchanged. No filesystem watcher, NLP, org chart, new state, prompt/output display or raw production logging is added.

### Automated verification (2026-10-08 Asia/Singapore)

- `uv run pytest -q`: **178 passed**, including **38 native contract tests** plus all 140 prior regressions; two existing Starlette/httpx/anyio deprecation warnings.
- `uv run ruff check backend main.py`: passed.
- `cd frontend && npm test -- --reporter=dot`: **29 passed / 12 files**.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.

Native tests include isolated Unix WebSocket negotiation/read-only controls, version mismatch, malformed/unavailable sources, explicit binding, replay, waiting, definition/nickname precedence, concurrency, snapshots/privacy, child recovery and parent exit. They are deterministic contracts, not provider capability verification. Existing State Fidelity real-process/fallback tests remain in the full suite.

### Real runtime smoke

Controlled disposable repositories exercised actual daemon **0.160.1** with CLI/TUI **0.160.0**, known thread UUIDs and real office-run registration. A separately owned diagnostic driver created fixture turns and supplied fixture answers; production consumers never controlled or answered the TUI. A first read-only turn materialized the native rollout before explicit TUI resume. The production binding API and consumer then observed:

1. Known Office `smoke-lead` bound to the selected native UUID and connected successfully.
2. Actual apply_patch changed calc.py from 41 to 42; native fileChange drove CODING and successful changed_files. The resulting file was independently checked.
3. Actual rg, shell printf and pytest completed successfully; normalized SEARCHING/TESTING/tool activity and native exit codes were observed.
4. Plan requestUserInput drove WAITING/user_input. Reconnecting while pending restored the same wait; resolution recovered without a new agent.
5. Actual subagent spawn created exactly one child Office Agent, with parent_agent_id=smoke-lead. Generated native nicknames differed between controlled runs; explicit child_definition_id=tester retained visible Tester, role tester and Run tests responsibilities. Actual native role was null.
6. Reconnect during child work produced no duplicate agent. Actual child completion displayed DONE before removal after three seconds.
7. Closing native observation and injecting discovery unavailability left the Office alive. A normalized ToolObserver fallback update drove TESTING; HTTP and WebSocket remained available. Chromium loaded the real production frontend, rendered one canvas, received a one-agent snapshot and reported no page errors under that disconnected condition.

Reviewed structural samples and final run details are in [NATIVE_RUNTIME.md](NATIVE_RUNTIME.md). Full logs/manifests/helpers remain ignored under runtime/probe. The real-browser disconnect checks use actual native smoke servers; a separate normalized fixture screenshot [native-waiting-details.png](images/native-waiting-details.png) verifies AgentPanel waiting/identity presentation, not provider capability.

Failed smoke startup attempts used an incorrect wrapper argument separator, tried resuming a fresh thread without a rollout, or reused a disposable tmux name before shutdown completed. These were fixture failures, corrected with proper arguments, an initial persisted turn and a unique owned socket. They are not passing evidence. An early native test expected a released baseline when a live fallback existed; the deliberate restored-fallback policy changed the expectation to immediately restored TESTING with ToolObserver provenance. No old regression assertion was removed or weakened.

Supported exact protocol profiles are 0.159.3/0.160.0/0.160.1; **only 0.160.1 has this production live smoke**. Prior profiles rely on Phase 3A evidence and reviewed schemas. Normal conversational/approval waits, multiple/empty child recipients, remote MCP semantics, stable native roles, continuous THINKING and natural-language result/task semantics remain unverified/partial. Long-running repeated reuse and oversize catch-up need broader future validation. See [the contract/limits](NATIVE_RUNTIME.md).

Phase 1 COMPLETE; Phase 2 COMPLETE; Phase 3A COMPLETE; Phase 3B v1 COMPLETE. Phase 3B v2 / Phase 4 NOT YET IMPLEMENTED.

## Completed Phase 3A Native Runtime Capability Probe

- Repeatable real Codex structured capture and selected-thread observing are opt-in and isolated.
- Recorded output is sanitized, private and ignored; no credentials, environments or unrelated message content are logged.
- Actual direct Codex normal turns, apply_patch editing, rg, shell and pytest were exercised.
- A legitimate unresolved contract explicitly triggered native request_user_input and waitingOnUserInput; direct and actual DevRouter input resolution were observed.
- Real subagent spawn, independent ID, native parent metadata, nickname, wait and completion were exercised in both paths. Native stable roles were null and are not invented.
- Installed DevRouter's actual tmux → office-run → Codex path was exercised; shared-daemon event visibility and the foreground process-tree limitation are documented.
- Every confirmed matrix claim has reviewed observed samples; partial/unavailable/unknown claims remain distinct. No heuristic is labeled native.
- State Fidelity/Semantic regressions pass; no production adapter, domain-state change or frontend change is included.

Verification (2026-10-02):

- `uv run pytest -q`: 140 passed, including 21 probe tests; two existing deprecation warnings.
- `uv run ruff check backend main.py`: passed.
- `cd frontend && npm test -- --reporter=dot`: 27 passed across 12 files.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.
- Public experiment CLI A–E: all five real turns completed; D requested input, E emitted child lifecycle. B's actual return value was independently verified as 42; C's commands exited successfully.
- Public capture pipeline: actual Codex and probe both exited 0. Public observe CLI: exited 0 against the live controlled DevRouter thread; its TUI remained active.
- DevRouter tools: actual rg/printf/pytest succeeded; a separate 45-second/10-ms scan of the wrapper's TUI PID yielded zero tool observations. Native history confirmed three successful command completions. Zero observations is a documented source limitation, not a test pass.

See [matrix](runtime-probe/CAPABILITY_MATRIX.md), [Codex sources/corrections](runtime-probe/CODEX.md), [DevRouter](runtime-probe/DEVROUTER.md) and [samples](runtime-probe/SAMPLES.md). Protocol-unavailable and malformed-input unit fixtures test the probe only; they do not verify provider capabilities. An additional default-mode input experiment ended with native errors and a failed turn; input capability in that mode remains unknown. The failed initial framing/filter/projector/fixture attempts are recorded in the source guide and excluded from passing evidence.

Phase 1 State Fidelity COMPLETE; Phase 2 Semantic Agent Model COMPLETE; Phase 3A COMPLETE; Phase 3B Native Adapter NOT YET IMPLEMENTED.

## Completed Semantic Agent Model

The completed phase satisfies:

- Legacy Agent payloads validate with safe semantic defaults.
- YAML project definitions load; duplicate IDs within one project fail clearly and definitions cannot leak across projects.
- A matching Tester runtime subagent appears with the semantic name, stable role, responsibilities, definition ID, and parent ID.
- Native metadata overrides project defaults; project defaults override wrapper metadata; generic fallback agents still work.
- Weaker/partial rediscovery preserves stronger identity and existing activity provenance.
- Backend agents retain roles while running pytest, search, or other tools.
- office-run flags/environment propagate semantic metadata and allow separate instances of one definition.
- Existing HTTP and WebSocket protocol shapes remain compatible.
- AgentPanel renders semantic identity and older agents; character labels use normalized names.
- OfficeScene and state-to-zone routing remain unchanged; no NLP, filesystem CODING detection, database, SaaS, or org chart is added.
- Both test suites, both linters, production build, and diff checks pass.

Smoke procedure: run a server with a Tester definition, register a runtime instance with `definition_id=tester` and `parent_agent_id=lead`, confirm the character name and details, then change task/state/tool and verify the role and parent remain stable. Unregistered instances retain fallback names. A parent need not be active to display its ID.

### Semantic verification evidence (2026-10-02)

| Criteria | Evidence |
| --- | --- |
| Safe defaults, YAML scope/matching, native precedence, passive protection, parentage, restart cleanup, stable roles | `backend/tests/test_semantic_identity.py` |
| Actual child environment, argument precedence, distinct instances, legacy launch behavior | `backend/tests/test_cli.py` |
| Passive metadata transport and isolation of invalid metadata | `backend/tests/test_adapters.py` |
| Legacy/semantic HTTP, snapshot and incremental WebSocket contracts | `backend/tests/test_api.py`, `frontend/src/api/websocket.test.ts` |
| Semantic details and legacy frontend rendering | `frontend/src/components/AgentPanel.test.tsx` |
| Existing activity, tool concurrency and real-process regression | Existing State Fidelity tests, including `backend/tests/test_live_fidelity.py` |

Required suite results:

- `uv run pytest -q`: 119 passed; two existing Starlette/httpx/anyio deprecation warnings.
- `uv run ruff check backend main.py`: passed.
- `cd frontend && npm test -- --reporter=dot`: 27 passed across 12 files.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.

Local browser verification uses the production build, a loopback FastAPI server with a Tester definition, and controlled normalized events. It confirms Tester details, responsibilities, parent ID, current assignment/state/tool, and stable semantics after tool completion. Screenshots are in `docs/images/semantic-agent-details.png` and `docs/images/semantic-agent-label.png`. Quota data is stubbed for these fixtures. This validates the local HTTP/WebSocket/UI integration, not a provider-specific native subagent feed or real model calls.

Early browser harness attempts assumed a fresh-start response on repeated registration, selected a moving character too soon, or used an incorrect event name. These fixture errors were corrected and are not counted as passing evidence. No test assertions or product behavior were weakened.

## Completed State Fidelity acceptance

The previous phase is complete; all of the following remain regression requirements.

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

## Verification evidence (2026-10-01)

| Criteria | Evidence |
| --- | --- |
| Typed provenance, legacy default, UTC timestamps, priority and recency | `backend/tests/test_provenance.py` |
| Wrapper and process source tags, wrapped identity, unwrapped discovery | `backend/tests/test_cli.py`, `backend/tests/test_adapters.py`, `backend/tests/test_observer_manager.py` |
| Tool source tags, concurrent tools, exec changes, launcher exclusion | `backend/tests/test_tool_observer.py` |
| Timeout protection and process cleanup | `backend/tests/test_provenance.py`, `backend/tests/test_live_fidelity.py` |
| Legacy HTTP payloads and snapshot/start/update/stop WebSocket shapes | `backend/tests/test_api.py` |
| Existing normalized frontend behavior | Existing frontend tests; frontend source unchanged |

Required suite results:

- `uv run pytest -q`: 93 passed; two existing Starlette/httpx/anyio deprecation warnings.
- `uv run ruff check backend main.py`: passed.
- `cd frontend && npm test -- --reporter=dot`: 23 passed across 11 test files.
- `cd frontend && npm run lint`: passed.
- `cd frontend && npm run build`: passed.
- `git diff --check`: passed.

The real-process automated smoke uses office-run, a blocking search child, actual pytest, FastAPI, and process/tool observers. It verifies a single identity, SEARCHING/TESTING, protection across multiple idle periods, and exit cleanup without model calls.

The manual checklist was also exercised with a real wrapped Codex session against a loopback server in a disposable repository. Codex ran a search and actual pytest successfully; both commands stayed observable longer than the configured idle timeout. Browser observation confirmed one agent, search/test state updates, the test-lab indicator, and removal after exit (including the frontend's existing five-second offline grace period). Browser automation used local Chromium and screenshots for inspection. No frontend redesign was needed.

Early verification found and corrected an overly strict smoke-fixture lifecycle-order assumption and an agent-launcher prompt misclassification. An initial read-only Codex attempt could not run pytest's temporary-file setup; the verified disposable-repository run used workspace-write permissions and preserved command failures. Those failed attempts are not counted as passing evidence.


## Phase 4A spatial team acceptance

- [x] Pure frontend planning separates home/destination without backend truth changes.
- [x] THINKING/IDLE use explicit role homes; absent/unknown roles safely use desks.
- [x] TESTING/SEARCHING/TOOL_RUNNING/CODING override home.
- [x] WAITING/user_input uses NEEDS YOU and `?`; generic waiting remains distinct.
- [x] Child coordination requires a nonempty, non-self normalized child ID; parentage alone is insufficient.
- [x] DONE immediately celebrates during existing terminal grace.
- [x] Distinct stable seats preserve walkability, routing, collisions and y ordering, including uneven frame cadence.
- [x] Normalized simulation uses the same scene path with pause/resume.
- [x] Controlled Chromium screenshots demonstrate role homes, Review/Test Lab/Library, multiple user waits, coordination, child DONE and shared zones.
- [x] No provider parsing, UUID/content display or native infrastructure work is introduced.

Required verification remains full backend/frontend tests, both linters, production build and git diff check locally, plus GitHub Backend and Frontend. Never merge failing required checks. Visual evidence is controlled normalized data, not a native capability claim: [homes](images/spatial-role-homes.png), [attention/team](images/spatial-attention-team.png), [completion](images/spatial-child-done.png).

UX limits: dense grids shrink characters/may hide labels; returning agents take free seats rather than indefinitely reserving empty places; coordination shares the lounge without an organization graph. Phase 4B remains unimplemented.

Phase 4A local verification (2026-10-08): `uv run pytest -q` 210 passed, two existing deprecation warnings; `uv run ruff check backend main.py` passed; `npm test -- --reporter=dot` 75 passed across 14 files; `npm run lint`, `npm run build` and `git diff --check` passed. Chromium fixture smoke completed with zero page errors; all three screenshots were inspected. Hosted check results are tied to the final PR commit.


## Phase 4B — Team Interaction & Coordination Cues

- [x] New child starts generate one transient delegation; duplicate starts and reconnect snapshots do not replay it.
- [x] Explicit visible child waits retain a live-endpoint coordination link; clearing waits or hiding/removing targets removes it.
- [x] Child DONE transitions produce one returning handoff; repeated DONE does not duplicate it or alter the parent.
- [x] ERROR has persistent `!` and brief local emphasis, without parent failure inference.
- [x] User attention remains strongest; ordinary parentage creates no permanent graph.
- [x] Store cue history, dedup keys and Pixi primitives are bounded; expiry/removal/unmount clean resources.
- [x] Scripted simulation uses shared normalized lifecycle messages; pause stops scripted changes without freezing TTL cleanup.
- [x] Existing spatial destinations/routing/collisions and semantic names remain; backend/native infrastructure is unchanged.
- [x] Controlled Chromium verifies duplicate start/DONE, TTL start/midpoint/expired states, moving coordination, handoff, simultaneous blocked/delegation, user attention, wait clear, project filtering, reconnect snapshots and offline cleanup.

Visual evidence under docs/images/interaction-*.png uses only normalized disposable fixture Agents, not private runtime content. Required local suites and hosted Backend/Frontend remain mandatory; exact hosted results belong to the final PR commit. Phase 4C is not implemented.

Phase 4B local verification (2026-10-08): `uv run pytest -q` 210 passed / two existing deprecation warnings; `uv run ruff check backend main.py` passed; frontend `npm test -- --reporter=dot` 90 passed / 16 files; `npm run lint`, `npm run build` and `git diff --check` passed. Final Chromium fixture smoke reports zero page errors and all eight timed screenshots were inspected. An early fixed 5.1s browser cleanup wait was too tight for message receipt plus the 250ms sweep; observing receipt and polling expiry corrected the fixture. No product assertions or grace duration were weakened. Hosted results are attached to the final PR commit.
