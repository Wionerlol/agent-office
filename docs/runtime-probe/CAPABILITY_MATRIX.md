# Phase 3A capability matrix

Phase 1 State Fidelity: **COMPLETE**. Phase 2 Semantic Agent Model: **COMPLETE**. Phase 3A Native Runtime Capability Probe: **COMPLETE**. Phase 3B Native Adapter: **NOT YET IMPLEMENTED**.

Evidence collected on 2026-10-02: installed Codex CLI **0.159.3**, shared daemon **0.160.0**, current configured model **gpt-6.1-sol** with medium reasoning. The daemon version was read with `codex app-server daemon version`; both binaries generated their own experimental protocol schemas. No runtime upgrade/restart was performed.

“Confirmed” means an actual controlled provider run emitted the stated fact. “Partial” means the fact exists but does not establish the entire requested semantic state. “Unavailable” is scoped to an exercised source/case. “Unknown/not exercised” is not a negative capability claim. Unit-test fixtures establish probe behavior only. Filesystem entries describe possibilities, not an implemented observer or collected evidence.

| Semantic signal | Native structured source | Wrapper | Process/Tool | Filesystem possible | Reliability | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Thinking | `item/started` + `item/completed`, `item.type=reasoning` in scenario D | Initial THINKING baseline | No direct model-phase fact | No | **Partial** | Reasoning items confirmed; ordinary A emitted active/turn events without reasoning. No continuous native THINKING status established. [S2](SAMPLES.md#s2-reasoning) |
| Coding | `fileChange` start/completion, path and patch kind | No editing phase | Shell/tool execution is not coding | Writes possible | **Partial state; confirmed edits** | No native status named CODING; edits are explicit facts. Shell-based edits may have different visibility. [S3](SAMPLES.md#s3-file-edit) |
| Testing | Generic command execution for actual pytest, successful exit | No specific testing signal | Existing ToolObserver observed test activity under standalone app-server | No reliable test state | **Partial semantic label** | No native TESTING event. Executable observation remains command classification; the daemon can execute outside the TUI PID subtree. [S4](SAMPLES.md#s4-tools) |
| Searching | Generic command execution for actual rg | No specific search signal | ToolObserver observed search activity in direct runs | No | **Partial semantic label** | No native SEARCHING event; short processes can be missed by polling. [S4](SAMPLES.md#s4-tools) |
| Waiting for user | `item/tool/requestUserInput`, `activeFlags=[waitingOnUserInput]`, `serverRequest/resolved` | Wrapper remains at baseline | No dependable distinction from inactivity | No | **Confirmed** | Direct Plan turn and real DevRouter TUI both exercised; observer never answered TUI requests. Default-mode input remains unknown after a provider-error failed turn; approval waiting is a separate, unexercised flow. [S5](SAMPLES.md#s5-user-input-required) |
| Waiting on child | `collabAgentToolCall`, `tool=wait`, inProgress/completed | No | OS children do not prove delegation | No | **Partial** | Native wait call confirmed; receiverThreadIds and agentsStates were empty. No dedicated waiting-on-child flag observed. [S6](SAMPLES.md#s6-subagents-and-delegation) |
| Subagent spawned | `subAgentActivity`, `kind=started`, `agentThreadId`; child metadata | Only explicitly provided parent/definition | OS subprocess is not a semantic subagent | No | **Confirmed** | Independent native child identity and parent reference; direct and DevRouter. [S6](SAMPLES.md#s6-subagents-and-delegation) |
| Subagent completion | Child `turn/completed`, activity `kind=completed`, parent wait completes | No native child lifecycle | Process exit is insufficient | No | **Confirmed completion; partial result delivery** | Parent final message follows; a structured child-result transfer was not established. [S6](SAMPLES.md#s6-subagents-and-delegation) |
| Subagent parent | `thread.parentThreadId`, `source.subAgent.thread_spawn.parent_thread_id` | `--parent` remains explicit optional metadata | Do not substitute PPID | No | **Confirmed** | Child metadata independently corroborates parent activity. [S6](SAMPLES.md#s6-subagents-and-delegation) |
| Subagent role/name | `agentNickname` populated; `agentRole` / `agent_role` null | Definitions/explicit roles still work | No stable role inference | No | **Name confirmed; role unavailable in observed cases** | Mendel/Averroes are generated nicknames, not Tester/Reviewer responsibilities. Custom configured native roles were not exercised. [S6](SAMPLES.md#s6-subagents-and-delegation) |
| Task update | New turn/userMessage, plan items; TUI `thread/goal/cleared` | Launch assignment only | No dependable semantic assignment | No | **Partial** | These are conversation/plan/goal facts, not an observed Agent.task update contract. Content is redacted. [S7](SAMPLES.md#s7-plans-and-conversation-context) |
| Tool start/finish | `commandExecution` started/completed; exec JSON `command_execution` items | Agent lifecycle only | Polling works when tools are descendants | No | **Confirmed native command lifecycle** | Tool identities/processId/exitCode available; not every MCP/tool family exercised. [S4](SAMPLES.md#s4-tools) |
| File edit | `fileChange`, `changes[].path`, `kind.type=update`, completed | No | Native patch need not spawn an OS child | Writes possible | **Confirmed apply_patch edit** | File contents changed in controlled fixtures. Diff/body intentionally redacted; no filesystem watcher. [S3](SAMPLES.md#s3-file-edit) |
| File read | Shell cat; commandActions=read (path), sometimes unknown | No | Command observation possible | Access events possible | **Partial** | Structured read annotation/path confirmed in E, not a distinct/universal file-read lifecycle. [S9](SAMPLES.md#s9-structured-file-read-annotation) |
| Idle / ready for input | `thread/status/changed`, `status.type=idle`; turn completed | Wrapped process still alive | Timeout is a weaker fallback | No | **Confirmed thread idle** | Idle is not the same fact as a suspended input request. [S1](SAMPLES.md#s1-turn-and-idle) |
| Generic WAITING | Input requests and native wait calls are distinct | No | Inactivity is ambiguous | No | **Normalization undecided** | No new AgentState or waiting_reason field in this phase. |

## Scenario results

- **A:** Direct `codex exec --json` and standalone app-server inspected the fixture without editing. Native turn start/completion confirmed; app-server idle confirmed. No reasoning item in ordinary A.
- **B:** Both direct structured sources observed apply_patch editing; native completed file-change path is calc.py. The repeatable A–E CLI fixture ended with answer=42 and actual pytest passing.
- **C:** rg, printf shell, and actual pytest each ran successfully in direct and DevRouter fixtures. Compare structured command facts with existing ToolObserver, rather than calling classification native state.
- **D:** A genuine undecided 43-versus-44 contract triggered request_user_input in Plan mode. The direct harness paused before supplying a fixture answer. DevRouter's original TUI supplied its answer with the passive observer connected; native resolution and turn completion were captured.
- **E:** Real spawn/delegation, child identity, parent metadata and completion were collected in both paths. Native roles were null. No fabricated OS-process subagents.
- **F:** Installed DevRouter launched actual tmux → office-run → Codex, preserved native events through the shared daemon, and added launch identity/lifecycle metadata. See [DEVROUTER.md](DEVROUTER.md).

## Phase 3B recommendation

Start with a thin, opt-in Codex app-server consumer, using version-specific protocol schemas and explicit selected-thread scope. Confirmed native facts should outrank structured observation, process/tool observation, filesystem fallback and heuristics; retain the existing EventSource/status arbitration and SemanticIdentityResolver.

- Bridge native thread IDs to office runtime IDs explicitly. A repository match alone is ambiguous when several agents share a workspace; this probe uses a uniquely controlled workspace and does not solve production binding.
- Track request IDs and exact waitingOnUserInput facts separately from idle and child wait; handle pending-request replay on reconnect. Any waiting_reason addition needs a separate decision in Phase 3B.
- Normalize fileChange and command lifecycle only after defining success/failure and concurrent-item semantics. Reasoning items establish reasoning activity, not coverage of every moment of model execution. Preserve lower-confidence fallback where native evidence is absent.
- Use native parent references; never OS PPIDs. Leave null roles absent so definitions can enrich them. Decide whether generated nicknames belong in diagnostic metadata or display names before letting them override stable definition names.
- Keep the daemon/TUI connection authoritative for responses. A monitoring client must never answer approvals/user input, alter config, start turns, load historical threads, restart the daemon, or turn a disconnect into agent death.
- Add reconnect, replay/deduplication, unsupported-version behavior and an explicit office/thread binding contract before production delivery. The Unix WebSocket/experimental protocol and nullable role fields remain material uncertainties.

No CodexNativeAdapter prototype or production normalization was needed for these conclusions.
