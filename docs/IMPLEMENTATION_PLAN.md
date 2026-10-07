# Codex Implementation Plan

## Phase state

1. State Fidelity — COMPLETE.
2. Semantic Agent Model — COMPLETE.
3. Phase 3A Native Runtime Capability Probe — COMPLETE: inspect installed CLI/daemon/DevRouter, isolate content-denying capture and selected-thread observation, exercise real A–F scenarios, publish reviewed matrix/samples, run regressions and prepare a PR.
4. Phase 3B Native Runtime Adapter v1 — COMPLETE. Explicit bindings, read-only versioned consumer, waiting context, semantic child normalization, bounded replay/reconciliation and concurrent activity aggregation are implemented. Full regression and real daemon/TUI smoke passed; preserve these gates for revisions.
5. Phase 3B v1.1 — COMPLETE: explicit-resume/operator CLI binding, generation-aware retries, per-thread recovery, reviewed profiles and local health diagnostics.
6. Phase 3B v2 / Phase 4 — NOT YET IMPLEMENTED. Prioritize explicit launcher binding ergonomics, version validation, per-thread failure isolation and long-running replay/reuse before new spatial features.

## Completed Phase 2: Semantic Agent Model

1. Extend Agent with safe semantic fields and introduce AgentDefinition.
2. Load project-scoped definitions in the existing YAML configuration.
3. Resolve semantic identity centrally during registration without changing status arbitration.
4. Propagate optional wrapper/environment metadata and parent/definition references.
5. Display semantic details using the existing frontend names and state routing.
6. Cover compatibility, priority, scope, parentage, and stable-role regressions.
7. Synchronize phase documents, run required verification, inspect the affected UI, and prepare a PR.

## Completed State Fidelity plan

## Objective

Implement explicit event provenance and authoritative state arbitration.

## Suggested sequence

1. Extend backend domain models with EventSource.
2. Add centralized source-priority/arbitration logic.
3. Teach OfficeRuntime to track and enforce status provenance.
4. Tag all existing event emitters:
   - office-run -> wrapper
   - ToolObserver -> tool_process
   - GenericProcessAdapter/process lifecycle -> process
   - idle timeout -> timeout
5. Add or adjust tests before broad refactoring.
6. Verify wrapped-agent de-duplication still holds.
7. Optionally expose status source in AgentPanel for diagnostics only.
8. Run the full verification matrix.

## Implementation principles

- Prefer small changes over architectural replacement.
- Keep provider-specific logic out of the frontend.
- Keep precedence policy testable and centralized.
- Preserve backward compatibility for POST /api/events.
- Do not silently change the meaning of existing state names.
- If a design choice is not specified, choose the simplest option and record it in docs/DECISIONS.md.

## Completion report

When finished, report:
- files changed;
- arbitration model implemented;
- edge cases handled;
- tests added/updated;
- exact verification commands and results;
- any remaining open questions or follow-up work.
