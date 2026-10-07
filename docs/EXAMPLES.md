# Agent Office Examples

## Phase 3A: inspect native facts before mapping states

GOOD: `item/tool/requestUserInput` plus `waitingOnUserInput` is an explicit user-input wait. Record the native request ID and resolution. Do not normalize it into generic WAITING during the probe phase.

GOOD: native `subAgentActivity.agentThreadId` and child `parentThreadId` establish an organizational child; its agentRole may be null while a project definition still provides Tester responsibilities.

BAD: rename a generated nickname such as Mendel to Reviewer because the requested assignment was review. Task text is not a permanent role; do not parse it into one.

BAD: turn an active thread into definite THINKING, every shell into CODING, or a daemon/process child into a semantic subagent. Native reasoning and patch items provide specific facts with explicit limits.

GOOD: capture a selected structured stream through `uv run python -m backend.probe capture`, or run controlled A–E experiments with `experiment --output-dir runtime/probe/run-01`. Keep debug logs ignored and publish only reviewed sanitized [samples](runtime-probe/SAMPLES.md). Phase 3A is complete; Phase 3B normalization remains unimplemented.

## Completed Semantic Agent Model examples

## GOOD: project-defined Tester subagent

```yaml
project:
  name: demo
  path: .
agents:
  - id: tester
    name: Tester
    role: tester
    responsibilities:
      - Run unit tests
      - Investigate failures
```

```bash
uv run office-run codex --definition tester --parent lead --task "Verify authentication changes"
```

The server uses the project definition to label this runtime instance Tester. Its definition is `tester`, its parent is `lead`, and its stable role/responsibilities survive activity changes. The wrapper generates a distinct instance ID for each definition-based launch unless `--id` is supplied.

## GOOD: explicit native identity overrides project defaults

An orchestrator posts `agent.started` with `source=native`. Its normalized Agent has `definition_id=tester`, `name=Security Tester`, `role=security`, `responsibilities=[Audit authentication]`, and `parent_agent_id=security-lead`. These explicit fields win over the Tester definition. Omitted fields still receive applicable project defaults.

## GOOD: Backend running pytest

```text
name = Backend Engineer
role = backend
responsibilities = [Own backend interfaces and behavior]
task = Verify authentication changes
status = testing
current_tool = pytest
```

Role remains backend. A future home zone can depend on role; the current destination still depends on TESTING.

## BAD: tool-derived permanent identity

Do not rename Backend Engineer to Tester or assign `role=tester` because pytest starts. Do not rename it Researcher because it runs rg. Prompts/tasks are not parsed to infer roles.

## GOOD: safe legacy fallback

An unregistered Codex process without semantic metadata retains its generic process name, nullable role/parent/definition, and empty responsibilities. A project declaration alone does not create a character. An explicitly requested unknown definition is retained for diagnostics and does not silently match another definition.

## Completed State Fidelity examples

## GOOD: stronger activity beats timeout

Current state:

```text
status = testing
status_source = tool_process
status_observed_at = 12:00:10
```

At 12:00:20 a timeout heuristic attempts:

```text
idle / source=timeout
```

Expected: keep TESTING.

Why: timeout is weaker evidence than observed test-process activity.

---

## GOOD: newer equal-authority update wins

```text
12:00:10 wrapper -> thinking
12:00:15 wrapper -> done
```

Expected final state: DONE.

---

## BAD: last writer wins regardless of source

```text
12:00:10 tool_process -> testing
12:00:11 timeout -> idle
```

Bad result: IDLE.

This makes the office visually lie about real work.

---

## GOOD: wrapped identity remains one agent

Process environment:

```text
AGENT_OFFICE_ID=backend
AGENT_OFFICE_NAME=Backend
AGENT_OFFICE_PROVIDER=codex
```

office-run posts agent.started for `backend`.

Generic process scanning later sees the Codex child.

Expected: one visible agent, id `backend`.

---

## BAD: duplicate wrapper and passive agents

Visible office:

```text
Backend
Codex 24891
```

when both refer to the same wrapped process.

---

## GOOD: provider-agnostic frontend

Backend receives some future Codex-native event and normalizes it to:

```json
{
  "type": "agent.state_changed",
  "agent_id": "backend",
  "source": "native",
  "payload": {"to": "waiting"}
}
```

Frontend only sees normalized status WAITING and moves the character accordingly.

---

## GOOD: coding from file activity

If filesystem observation is implemented:

```text
agent repository: /repo
modified: /repo/backend/api.py
source: filesystem
```

Possible normalized result:

```text
CODING
```

provided no stronger recent state such as TESTING should remain authoritative.

---

## BAD: noisy filesystem events

Do not infer CODING from:

```text
.git/*
node_modules/*
frontend/dist/*
.venv/*
runtime/events.jsonl
```
