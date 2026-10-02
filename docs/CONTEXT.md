# Agent Office Context

## Current repository state

Agent Office is already beyond an initial visual prototype.

Backend:
- Python 3.13
- FastAPI
- Pydantic
- psutil
- OfficeRuntime + AgentRegistry + EventBus
- GenericProcessAdapter
- office-run wrapper
- ToolObserver
- Codex usage monitor

Frontend:
- React 19
- TypeScript
- Zustand
- PixiJS
- routing and collision handling
- desk assignment
- office scenery
- state-driven spatial behavior
- Codex usage atmosphere

## Current runtime path

Typical wrapped flow:

```text
DevRouter
  -> office-run
      -> Codex
      -> POST normalized lifecycle events
      -> environment identity metadata

Agent Office server
  -> GenericProcessAdapter
  -> ToolObserver
  -> OfficeRuntime
  -> EventBus
  -> WebSocket
  -> Zustand
  -> PixiJS OfficeScene
```

DevRouter should be run directly when integrated with Agent Office. Do not wrap DevRouter itself in office-run.

## Historical State Fidelity weakness (resolved)

Before State Fidelity, the backend combined several evidence sources without explicit authority.

Examples:
- office-run marks starting/thinking/done/error;
- GenericProcessAdapter discovers processes;
- ToolObserver infers testing/searching/tool_running from child commands;
- ObserverManager derives idle from inactivity.

That phase introduced typed EventSource, centralized source precedence, internal status/registration evidence, lifecycle PID guards, and concurrent tool handling. Decisions 1–10 record the implemented contract.

## Important implementation restraint

Do not rewrite OfficeScene, routing, collision, or general frontend architecture for this phase.

Do not convert the project into a complex event-sourcing platform.

The goal is a small, understandable arbitration layer suitable for a local developer tool.

## Completed Semantic Agent Model phase

The completed semantic phase added stable identity: provider/process names alone did not explain responsibilities or subagent ownership.

AgentDefinitionRegistry loads repository-scoped definitions from the existing server YAML. SemanticIdentityResolver enriches registration centrally and keeps identity evidence separate from activity evidence. GenericProcessAdapter transports optional environment metadata; office-run supplies explicit flags/environment. Native/orchestrator integrations can post normalized Agent fields with source=native. No provider-specific native subagent adapter is added in this phase.

Frontend labels already consume agent.name. AgentPanel adds responsibilities, parent ID, and separate current task/state/tool. The existing state-to-destination interface is unchanged and can coexist with a future role-to-home-zone mapping.

Project definitions are static until the server reloads. Parent references may point to an unobserved/exited agent and are informational; there is no inferred hierarchy or cascade cleanup. Role strings stay free-form for compatibility. No task/prompt inference or filesystem observer is implemented.

Future work may include provider-specific native subagent normalization, explicit semantic edit/clear operations, definition hot reload, or role-based home zones. These are outside the current completion criteria.

## Phase 3A completed: evidence before native integration

State Fidelity and Semantic Agent Model are complete. Phase 3A adds only an opt-in diagnostic probe and sanitized runtime evidence; Phase 3B Native Adapter is not yet implemented. See `docs/runtime-probe/` before designing it.

The inspected CLI is 0.159.3; the running shared daemon is 0.160.0. Standalone stdio/exec JSONL and the real DevRouter daemon Unix WebSocket were exercised. Native waitingOnUserInput/request/resolve, fileChange, commandExecution, subAgentActivity and parent metadata are real facts. Ordinary active turns do not establish continuous thinking/coding, and native roles were null. Generated nicknames do not supply responsibility semantics.

In the current shared-daemon path, tool execution can occur outside office-run's foreground TUI PID subtree. Its controlled 45-second ToolObserver scan produced no tool observations despite native history confirming successful rg/shell/pytest. This is new runtime capability evidence, not a change to the existing observer/arbitration code. A future adapter must bind office runtime identity to native thread identity explicitly and handle version differences, reconnect replay and missing metadata without inventing facts.

Native IDs are pseudonymized in probe output. Free text/diffs/arguments/account/environment content are denied before persistence. Full captures and disposable manifests stay under ignored runtime/probe; only minimal reviewed extracts are checked in. There is no raw-event frontend protocol or schema change.
