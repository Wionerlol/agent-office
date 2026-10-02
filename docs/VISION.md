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

The current bottleneck is not scenery or rendering quality. It is state fidelity.

The next implementation phase should make the answer to “what is this agent actually doing?” more accurate by introducing explicit event provenance, source priority, and conflict handling.

## Long-term product language

Runtime facts may become spatial or environmental signals rather than dashboard numbers.

Examples:
- tests running -> Test Lab activity;
- tests failing -> Test Lab warning state;
- agent waiting for user -> character moves to a user-attention area;
- heavy usage / low remaining quota -> office atmosphere changes;
- many active agents -> busier office ambience;
- PR ready -> review-oriented behavior.

These are future extensions. The immediate implementation must first make runtime state trustworthy.
