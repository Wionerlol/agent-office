# Codex runtime sources and repeatable capture

## Installed sources

On 2026-10-02, the CLI reports 0.159.3 and the already-running daemon reports 0.160.0. `codex exec --help` exposes --json; `codex app-server --help` exposes stdio and Unix/WebSocket transports and version-specific schema generation. These interfaces were inspected locally before experiments.

1. **exec JSONL:** Actual `thread.started`, `turn.started`, `item.started`, `item.completed`, `turn.completed`, command_execution and file_change records. A separate opt-in job source, not a transparent tap of the normal TUI.
2. **Standalone app-server stdio:** A diagnostic client initialized a real server, created a controlled workspace-write thread, and ran A–E. Structured turn/item/status and bidirectional input requests were received. No raw Responses API opt-in.
3. **Shared daemon Unix WebSocket:** HTTP Upgrade over the local control socket, initialize/initialized, metadata read, then thread/resume with excludeTurns=true and no config overrides. This subscribed to the already-loaded DevRouter thread. It emitted native notifications and server requests without requiring TUI stdout scraping. Closing the probe did not stop the TUI/daemon.
4. **Explicit session history:** A selected controlled DevRouter thread exposes a JSONL path with session_meta/event_msg records and provider timestamp/ordinal. Its history mode is paginated. This does not establish that legacy rollout tailing is a complete/live event bus; live capture prefers the app-server. No arbitrary history search, database inspection or filesystem watcher is added.
5. **MCP:** Actual startup status notifications and schema-defined tool/request/elicitation surfaces were found. Remote MCP tools/auth elicitation were not exercised; schema presence alone is not a confirmed semantic capability.

The [official app-server transport/schema documentation](https://learn.chatgpt.com/docs/app-server) corroborates stdio JSONL, Unix WebSocket framing and generated version-specific schemas. All capability conclusions in the matrix come from local experiments, not that documentation.

## Repeatable commands

Inspect the installed executable and daemon without changing them:

```bash
codex --version
codex app-server daemon version
codex app-server generate-json-schema --experimental --out /tmp/office-codex-schema
```

Run controlled real model experiments (uses existing Codex authentication; creates a disposable committed Git fixture):

```bash
uv run python -m backend.probe experiment --output-dir runtime/probe/run-01
# A smaller explicitly selected run:
uv run python -m backend.probe experiment --output-dir runtime/probe/run-02 --scenarios D E
```

The experiment harness answers the fixture arithmetic question after observing a real native request and waiting two seconds. It declines unexpected command/file approvals. These responses are confined to its own diagnostic thread. They are not monitoring behavior. Native and existing ToolObserver records are saved separately. Per-scenario console results describe observed methods/items; absence of a signal remains absence and is not converted into success.

Capture exec JSONL immediately through the sanitizer, without a raw-log tee:

```bash
set -o pipefail
codex exec --json --sandbox read-only -C /tmp/controlled-repo \
  'Read calc.py and explain it; do not edit or use remote tools.' \
  2>/dev/null | uv run python -m backend.probe capture \
  --source codex-exec --workspace /tmp/controlled-repo \
  --output runtime/probe/exec-01.jsonl
```

Both pipeline exit statuses matter. A provider failure is not successful verification. Repeat with a new output filename: existing logs are never overwritten.

For an existing selected native thread, use the socketPath from daemon version and the native thread ID (not the office Agent ID):

```bash
uv run python -m backend.probe observe \
  --socket /path/to/app-server-control.sock --thread NATIVE_THREAD_ID \
  --workspace /tmp/controlled-repo --duration 60 \
  --output runtime/probe/observe-01.jsonl
```

The probe reads metadata first and refuses an unrelated workspace or an unloaded/historical thread. Scope expands only from explicit native parent/child identifiers. It never submits turns, changes settings or replies to requests on this path. Selected child metadata is read to retain names and parentage. Pending input requests may be replayed on subscription; request/item IDs correlate them.

An explicitly selected history/structured JSONL file can be projected with capture --source codex-rollout --input /path/to/selected.jsonl. It is an offline diagnostic read, not a filesystem activity detector.

## Probe isolation and safety

`backend/probe/` is not imported by OfficeRuntime, observer startup, the API or frontend. Probe source names and envelopes are diagnostic strings, not EventSource additions. JSONL records preserve receipt sequence, UTC receipt timestamp, native timestamp/ordinal when supplied, exact event names, nested item/status types and relevant identity/relationship structure.

Native IDs are consistently pseudonymized. Workspace paths are relative; outside paths are hidden. Prompt/task text, messages, reasoning, answers, diffs, output, encrypted content and arguments are redacted. Commands retain only a bounded executable-token hint, never their arguments/body/output. Unknown fields are dropped, including environments/credentials/config/account details. Nicknames and roles are bounded metadata; credential-like strings are rejected. No stderr/terminal transcript is logged by the probe.

Files are created exclusively with mode 0600. Use the ignored runtime/probe directory; the entire directory, including manifests/fixtures/logs, is ignored. Full native content is never written to probe logs, even locally. Review minimal excerpts before publishing. Codex's own session persistence remains its existing behavior and is not altered by this diagnostic tool.

Structured payloads are deliberately projected, not lossless archives. Free-text tools/tasks cannot be reconstructed; unknown fields, excessive nesting and lists beyond 100 entries are omitted/bounded. Oversized or malformed input becomes a diagnostic malformed record without the original content. app-server normally supplies no per-notification native timestamp, so receipt time must not be mislabeled execution time.

## Verification limits and corrections

The protocol is experimental. No upgrade, daemon restart, remote listener, database, frontend change or domain adapter was introduced. The wrapper/observer architecture remains unchanged.

Early capture incorrectly flattened nested status/patch-kind objects and missed agentThreadId; the projector was corrected and D/E were exercised again with real provider events. A raw stdio initialize sent through app-server proxy timed out because the control socket requires a WebSocket Upgrade. The corrected Unix WebSocket connection succeeded. A CLI-only sourceKinds filter missed a live TUI whose source was vscode; workspace-scoped loaded metadata identified it. The initial DevRouter Git fixture lacked HEAD and office-run could not start; adding the fixture's initial commit fixed the experiment. These attempts are not counted as passing native verification.

An additional default-mode input experiment emitted native error notifications and ended with turn status failed, before any input request or successful model response. It is not counted as passing verification and does not establish that default-mode input is unsupported. Its error content was redacted; the provider cause is unclassified. Waiting-for-user evidence is confirmed for the exercised Plan workflow, while default-mode and approval workflows remain unverified. No blind retry was used to replace that failure.
