# Agent Office Acceptance Criteria

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
