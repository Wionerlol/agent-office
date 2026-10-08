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

That phase added lightweight project definitions and parent references, with semantic names on existing characters and details in AgentPanel. Phase 4A separates role homes from temporary activity destinations. Organization charts remain out of scope.

Phase 3A Native Runtime Capability Probe is complete. Its evidence report distinguishes native facts from structured observations and process/heuristic fallbacks. The real Codex/DevRouter path exposes explicit user-input waiting, file-change/command lifecycles and subagent parentage; it does not establish continuous THINKING/CODING coverage or stable native roles. See [the capability matrix](runtime-probe/CAPABILITY_MATRIX.md).

Phase 3B Native Adapter v1 is complete. It adds explicit native thread binding, user-input waiting, organizational child relationships and native command/file activity through the two completed foundations. Explicit native fact > structured runtime observation > process/tool observation > filesystem fallback > heuristic inference remains the principle. Reasoning coverage remains partial; no prompt/task NLP is introduced. See [the native runtime contract](NATIVE_RUNTIME.md).

## Long-term product language

Runtime facts may become spatial or environmental signals rather than dashboard numbers.

Examples:
- tests running -> Test Lab activity;
- tests failing -> Test Lab warning state;
- agent waiting for user -> character moves to a user-attention area;
- heavy usage / low remaining quota -> office atmosphere changes;
- many active agents -> busier office ambience;
- PR ready -> review-oriented behavior.

Test Lab activity, user attention and usage atmosphere are implemented. Failure-specific room signals, busier ambience and PR-ready behavior remain future extensions. Phase 4A adds role homes and attention/coordination interpretation on top of the runtime-state foundation.

Phase 3B v1.1 hardens daily operation: explicit launch identity enables a low-friction binding handshake, per-thread degradation preserves unrelated work, and local diagnostics distinguish integration health from agent activity. Fresh-session correlation remains unsupported without an explicit native identity; Phase 4A is implemented; Phase 4B interaction cues are implemented; Phase 4C daily-use readability is implemented.


## Phase 4A: spatial team behavior

Stable roles now give agents a recognizable home: Test Lab for Testers, Library for Researchers, Review Area for Reviewers, and desks for engineers/leads. Current work temporarily overrides home. Explicit user-input waiting brings agents to NEEDS YOU; deterministic child waiting uses coordination. Completion celebrates in place during existing grace. These are interpretations of normalized truth, without provider content or runtime inference. Phase 4B interaction cues are implemented; Phase 4C daily-use readability is implemented.


## Phase 4B: confirmed team interaction

Space now communicates collaboration as well as activity: a newly started child can receive a brief directional delegation pulse; an incremental DONE child returns a completion pulse; explicit child waiting retains a quiet coordination link. ERROR has a persistent exclamation marker and short failure emphasis. User attention remains strongest. These are content-free interpretations of normalized relationships/transitions, never a permanent org graph or a new backend fact. Phase 4C daily-use readability is implemented.


## Phase 4C: glance, focus and return

The office now supports daily inspection: select a semantic Agent, read its direct explicit context, navigate related Agents in details, and return to the whole office with Escape or an empty-area click. Priority labels preserve attention/ERROR/selection in crowded zones while unrelated characters stay visible. Keyboard Team controls and system reduced motion express the same facts. Laptop-width details stack beneath the complete scalable office. Runtime truth, spatial destinations and transient interaction meaning remain separate and unchanged.
