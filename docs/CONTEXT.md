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

## Existing weakness

The backend currently combines several evidence sources without explicit authority.

Examples:
- office-run marks starting/thinking/done/error;
- GenericProcessAdapter discovers processes;
- ToolObserver infers testing/searching/tool_running from child commands;
- ObserverManager derives idle from inactivity.

These sources can describe the same agent but do not currently carry explicit provenance into the runtime.

## Important implementation restraint

Do not rewrite OfficeScene, routing, collision, or general frontend architecture for this phase.

Do not convert the project into a complex event-sourcing platform.

The goal is a small, understandable arbitration layer suitable for a local developer tool.

## Open questions

These do not block implementation.

1. Whether API/manual events should have a dedicated precedence between wrapper and tool_process or remain a neutral compatibility source.
2. Whether status provenance belongs in first-class Agent fields or internal metadata.
3. Whether filesystem-derived CODING should ship in this phase or immediately follow it.
4. Whether future native Codex events will arrive through office-run, another adapter, or a dedicated integration.

Choose the simplest design that preserves future extensibility and document any choice made.
