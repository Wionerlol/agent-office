# Agent Office Vision

## Why this project exists

Agent Office turns local coding-agent activity into a spatial, glanceable office rather than another status dashboard.

The user should be able to look at the office and understand, without reading logs:

- who is actively working;
- who is testing or searching;
- who is waiting for input;
- who is blocked or failed;
- who has finished;
- whether the overall runtime is busy, quiet, or under pressure.

The product is local-first and optimized for a single developer running several coding agents across repositories.

## Product experience

Agent Office should feel like a live miniature workplace driven by real agent activity.

It should **not** feel like:
- a fake simulation whose animations are only loosely related to runtime facts;
- a generic monitoring dashboard with decorative sprites;
- a SaaS control plane;
- a provider-specific Codex UI.

It should feel like:
- a spatial projection of the agent runtime;
- a system where state changes cause meaningful movement and animation;
- an observatory where environment, room usage, and character behavior communicate system state;
- a provider-agnostic frontend driven by normalized domain events.

## Core philosophy

Backend owns runtime truth. Frontend owns visual interpretation.

The frontend should understand normalized concepts such as `Agent`, `AgentState`, and `AgentEvent`, not Codex-specific internals.

The system should prefer high-confidence, explicit runtime facts over inference. Heuristics are useful fallbacks, but must not silently override better sources.

## Current direction

State Fidelity is complete: explicit provenance and source arbitration make activity trustworthy. Preserve that foundation.

Semantic Agent Model is also complete. The office should communicate who each agent is, its stable responsibility, and which parent owns a subagent, alongside what it is doing. A project-defined Tester or Reviewer is more meaningful than a generic Codex process name.

Keep role (stable responsibility), task (current assignment), state (runtime activity), and tool (executable) separate. A Backend Engineer running pytest stays a Backend Engineer. Semantic identity comes from explicit runtime metadata and project definitions, never from current tool use or prompt inference.

That phase added lightweight project definitions and parent references, with semantic names on existing characters and details in AgentPanel. State continues to determine current destinations. Role-based home zones and organization charts remain future work.

Phase 3A Native Runtime Capability Probe is complete. Its evidence report distinguishes native facts from structured observations and process/heuristic fallbacks. The real Codex/DevRouter path exposes explicit user-input waiting, file-change/command lifecycles and subagent parentage; it does not establish continuous THINKING/CODING coverage or stable native roles. See [the capability matrix](runtime-probe/CAPABILITY_MATRIX.md).

Phase 3B Native Adapter is not yet implemented. Its design must start from these runtime facts, preserving the two completed foundations and the principle explicit native fact > structured runtime observation > process/tool observation > filesystem fallback > heuristic inference. No prompt/task NLP is introduced.

## Long-term product language

Runtime facts may become spatial or environmental signals rather than dashboard numbers.

Examples:
- tests running -> Test Lab activity;
- tests failing -> Test Lab warning state;
- agent waiting for user -> character moves to a user-attention area;
- heavy usage / low remaining quota -> office atmosphere changes;
- many active agents -> busier office ambience;
- PR ready -> review-oriented behavior.

These remain future extensions. The current implementation adds semantic identity on top of the completed runtime-state foundation.
