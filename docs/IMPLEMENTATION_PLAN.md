# Codex Implementation Plan

## Phase state

1. State Fidelity — COMPLETE.
2. Semantic Agent Model — COMPLETE.
3. Phase 3A Native Runtime Capability Probe — COMPLETE: inspect installed CLI/daemon/DevRouter, isolate content-denying capture and selected-thread observation, exercise real A–F scenarios, publish reviewed matrix/samples, run regressions and prepare a PR.
4. Phase 3B Native Runtime Adapter v1 — COMPLETE. Explicit bindings, read-only versioned consumer, waiting context, semantic child normalization, bounded replay/reconciliation and concurrent activity aggregation are implemented. Full regression and real daemon/TUI smoke passed; preserve these gates for revisions.
5. Phase 3B v1.1 — COMPLETE: explicit-resume/operator CLI binding, generation-aware retries, per-thread recovery, reviewed profiles and local health diagnostics.
6. Fresh-session deterministic correlation investigation — COMPLETE, investigation-only: current-runtime limitation; no Phase 3B v1.2 feature. See [evidence and decision matrix](runtime-probe/FRESH_SESSION_CORRELATION.md), Decision 28 and the explicit operator workflow in NATIVE_RUNTIME.md.
7. Phase 4A Role-Aware Spatial Team Behavior — COMPLETE: planner, role homes, attention/coordination, stable seats, DONE celebration, simulation and visual verification.
8. Phase 4B — NOT YET IMPLEMENTED. Refine readability/interaction separately. Native work requires new upstream evidence or a separately scoped correctness issue.

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


## Completed Phase 4A plan

1. Preserve backend/native contracts and inspect existing scene/pathing.
2. Add pure home/destination planning and exact aliases.
3. Add Review/User Attention anchors; reuse lounge coordination.
4. Allocate stable seats and apply meaningful plan changes incrementally.
5. Preserve routes/separation/terminal grace; recover stalled or displaced actors.
6. Update normalized simulation and pause/resume controls.
7. Verify deterministic frontend behavior and inspect real browser fixture screenshots.
8. Run full regressions and required Backend/Frontend CI; prepare a separate PR.
