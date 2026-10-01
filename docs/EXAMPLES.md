# Agent Office Examples

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
