# Agent Office Examples

## Phase 3B native normalization

GOOD: explicitly bind Office `lead` to a known native UUID. A second agent in the same repository stays unbound unless its own UUID is supplied. Repository matching alone must never select a thread.

GOOD: native nickname Gibbs plus explicit child_definition_id=tester yields visible Tester, role tester, responsibilities from the project, and parent_agent_id=lead. Native nickname remains metadata and null role erases nothing.

GOOD: requestUserInput produces WAITING with waiting_reason=user_input. An idle notification does not erase the request; resolution clears context. Replayed requests reconstruct an existing wait without duplicate child registration or repeated unchanged display.

GOOD: native pytest remains TESTING while a file change begins/ends. Only completing the last active operation returns to the surrounding baseline. A live process fallback test is restored when the native operation releases its evidence.

BAD: every parent with an active child becomes WAITING, native idle becomes waiting for a user, or reasoning absence becomes proof that the model is not thinking. Empty native wait recipients remain partial evidence.

GOOD: unsupported daemon version/disconnect leaves wrapper/process behavior operational. Production closes only its observation socket and does not answer a user request, restart a daemon, expose prompts, or mark an agent dead because observation was lost.

## Phase 3A: inspect native facts before mapping states

GOOD: `item/tool/requestUserInput` plus `waitingOnUserInput` is an explicit user-input wait. Record the native request ID and resolution. Do not normalize it into generic WAITING during the probe phase.

GOOD: native `subAgentActivity.agentThreadId` and child `parentThreadId` establish an organizational child; its agentRole may be null while a project definition still provides Tester responsibilities.

BAD: rename a generated nickname such as Mendel to Reviewer because the requested assignment was review. Task text is not a permanent role; do not parse it into one.

BAD: turn an active thread into definite THINKING, every shell into CODING, or a daemon/process child into a semantic subagent. Native reasoning and patch items provide specific facts with explicit limits.

GOOD: capture a selected structured stream through `uv run python -m backend.probe capture`, or run controlled A–E experiments with `experiment --output-dir runtime/probe/run-01`. Keep debug logs ignored and publish only reviewed sanitized [samples](runtime-probe/SAMPLES.md). Phase 3A is complete; Phase 3B normalization is described separately in NATIVE_RUNTIME.md.

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

## v1.1 explicit launch and health

GOOD: `office-run codex --id lead --native-child-definition tester resume UUID` registers then binds using the same explicit UUID and Office generation, without curl. `devrouter --office -- resume UUID` performs the same deterministic handshake through its installed wrapper. `agent-office native bind lead UUID` is the explicit operator alternative.

GOOD: a malformed Tester snapshot shows degraded/fallback active while Lead and Reviewer remain connected; retry reconstructs only Tester. A transport disconnect releases the owned root connection, while another root keeps native activity. Integration degraded is not AgentState.ERROR.

BAD: newest thread, only visible thread, same CWD or OS proximity selects a native identity. A fresh TUI without explicit identity remains unbound. Generated nickname/null role still never replace Tester responsibilities.

GOOD: `agent-office native validate --thread UUID` reports structural check names with no questions/output/patches. Unknown versions report review_required instead of silently enabling production parsing.


## Phase 4A spatial examples

| Normalized Agent | Home | Destination/behavior |
| --- | --- | --- |
| Tester, THINKING | Test Lab | Test Lab contemplation |
| Researcher, THINKING | Library | Library contemplation |
| Reviewer, THINKING | Review Area | Review contemplation |
| Backend, THINKING | Desk | Desk contemplation |
| Backend, TESTING | Desk | Test Lab workstation |
| Tester, SEARCHING | Test Lab | Library |
| Researcher, CODING | Library | Desk |
| Tester, WAITING/user_input | Test Lab | NEEDS YOU with `?` |
| Lead, WAITING/child_agent with Tester ID | Desk | Lounge coordination, Child wait |
| Lead, generic WAITING | Desk | General lounge waiting |
| Child, DONE | Role home | Immediate celebration at current position |

GOOD: several Testers keep distinct seats when a Researcher updates. Unknown `custom specialist` uses a desk. Backend-supplied semantic names remain visible.

BAD: infer role from pytest; send a testing Reviewer home instead of Test Lab; infer waiting from parentage; display questions/UUIDs; reshuffle everyone on unrelated updates.

Pause the normalized demo to inspect roles; Resume exercises the same live scene path. Reviewed screenshots: [role homes](images/spatial-role-homes.png), [attention/team](images/spatial-attention-team.png), [completed child](images/spatial-child-done.png).


## Phase 4B team interaction examples

GOOD: incremental Tester start with visible Lead parent emits one 3s Lead → Tester arrow. Duplicate start does not replay it. A reconnect snapshot containing that same pair emits no arrow.

GOOD: Lead WAITING/child_agent on visible Tester has a quiet moving-endpoint `↔` link. Lead returning to THINKING removes it. If Tester is filtered out, Lead retains its local Child wait marker without a fabricated endpoint.

GOOD: Tester TESTING → DONE emits one returning `✓`; DONE → DONE emits none. The parent neither moves nor changes status because of the handoff. Ordinary parentage without an active wait produces no permanent line.

GOOD: Reviewer enters ERROR, receives a brief ring and a persistent `!` while ERROR lasts. The Lead remains healthy unless its own normalized state says otherwise. NEEDS YOU remains stronger than team packets.

BAD: infer delegation from similar tasks, animate all children on snapshots, retain organization lines, expose questions/errors in bubbles, or reroute parents for transient cues.

See controlled normalized browser evidence: [delegation](images/interaction-delegation-midpoint.png), [moving coordination](images/interaction-coordination-moving.png), [coordination and user attention](images/interaction-coordination.png), [handoff](images/interaction-handoff.png), [simultaneous signals](images/interaction-multiple-blocked.png), [expired emphasis](images/interaction-blocked-expired.png). Start/midpoint/expired delegation states are also retained for timing inspection.


## Phase 4C daily inspection examples

GOOD: select Tester. Tester gets a warm full semantic label; its Lead parent and current waiting relation stay emphasized. Backend/research peers are quieter even when they share a repository, while Frontend NEEDS YOU and Reviewer ERROR remain obvious. Select Lead in the Parent Agent row, then use the Children/Waiting on buttons to return to Tester.

GOOD: crowded Test Lab keeps a selected Test Partner label readable without reseating the team. Hover exposes full semantic name and role/status; keyboard Team buttons provide the same inspection with Tab, Enter/Space and Escape. Panel close restores focus to that Agent's Team button.

GOOD: an active selected handoff becomes clearer but expires at its original deadline. A reconnect snapshot still generates no historical animation. A filtered target has no connector/navigation name; the panel says Not in this view.

GOOD: reduced-motion mode retains static ?, !, → and ✓, with short route travel and original cue lifetime. At 800/1024px, details appear below the complete scaled office; at 1280/1440px, they remain beside it.

BAD: selection changes seats/routes; same role/task/repository creates a team; focus hides a user-input waiter; hover exposes raw command/question/error content; selection restarts delegation; ordinary parentage becomes permanent graph lines.

Reviewed normalized browser evidence: [whole office](images/readability-whole-office.png), [selected Tester](images/readability-selected-tester.png), [selected Lead](images/readability-selected-lead.png), [crowded selected label](images/readability-crowded-selected.png), [800px layout](images/readability-800.png), [reduced-motion delegation](images/readability-reduced-delegation.png).
