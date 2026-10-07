# DevRouter → office-run → Codex observations

The installed DevRouter terminal module constructs a separate tmux server/session, launches the real Codex TUI, and optionally prefixes office-run with an explicit project session ID, display name, role Development, task DevRouter development session, and repository. Provider arguments follow `codex --`. This code was inspected in the installed package; no DevRouter files were modified.

## Actual experiment

A disposable committed repository, isolated DevRouter home/bridge and loopback Agent Office server were used. DevRouter was launched normally with --office from a real PTY. Its real TUI inspected calc.py, applied a patch, ran rg, a shell printf and actual pytest. A subsequent Plan turn asked for an unresolved result (43 or 44), then genuine native subagent delegation was requested. The TUI, not the observer, answered the input request.

The diagnostic client attached over the existing daemon's Unix WebSocket and subscribed only to the controlled loaded thread, without config/input overrides. Native fileChange and commandExecution start/completion, waitingOnUserInput, item/tool/requestUserInput, serverRequest/resolved, child activity and metadata were collected. The original TUI continued executing while the probe was connected and after it closed. Samples are in [SAMPLES.md](SAMPLES.md).

## Differences that matter

| Direct source | DevRouter path |
| --- | --- |
| exec --json provides a non-interactive structured stdout job stream | Normal DevRouter uses the interactive TUI inside tmux; stdout is a terminal, not JSONL |
| Standalone app-server is CLI version 0.159.3 and owned by the experiment client | The shared daemon actually reports 0.160.0; authored child metadata carries that version |
| The harness can answer its own bidirectional requests | The observer must leave requests to the original TUI; pending requests may replay on attach |
| Direct standalone tools were observable beneath the app-server process | Tool execution is delegated to the shared daemon, outside the wrapped TUI subtree; see tool-only experiment below |
| No office wrapper identity unless deliberately wrapped | office-run adds stable office identity/environment and launch lifecycle, but no native thread UUID binding or turn/input/subagent normalization |

Native structured facts survive DevRouter. Its tmux/office-run layer does not add a native semantic bus and does not need to parse terminal output. The normal wrapper sends STARTING/THINKING and final lifecycle states; its generic launch role/task are not native subagent role/task evidence.

The observed parent source was **vscode** despite this being a Codex TUI workflow; selected child originator was **codex-tui**. Do not assume sourceKinds=cli selects every CLI workflow. A probe's known controlled workspace is sufficient for this experiment, but production office-ID/native-thread binding is still an open Phase 3B contract.

The controlled native child had nickname **Averroes**, parentThreadId matching the TUI, agentRole=null, and sessionId matching its parent. Another direct snapshot from an earlier run used a different sessionId shape; preserve these fields as delivered rather than deriving a tree from sessionId alone. First-class parent metadata and subAgentActivity establish the relationship.

## Process comparison and exclusions

The direct app-server probe scanned its actual root at 10 ms using the unchanged ToolObserver; it collected search/test tool lifecycle classifications as well as host/sandbox startup processes. These are process observations, not native semantic labels. Fast commands such as printf can finish between scans.

A separate DevRouter tool-only experiment scanned the exact PID registered by office-run at 10 ms while real rg/printf/pytest ran. It produced **zero tool events** during the 45-second scan while the controlled tool-only turn completed all three commands. The exact latest turn was read through native paginated history: three commandExecution items, all exitCode=0; actual pytest passed once in 0.40 s. This is a visibility limitation, not a successful process observation. The native live listener for this follow-up attached after completion and contributed no lifecycle events; historical snapshots are labeled as such. The native source remains necessary when tools are hosted by the daemon rather than descended from the foreground TUI.

Alt+Q goes to an independent ChatGPT browser workflow. Its popup/native bridge is not Codex history. This was established by inspecting the installed command routing; no ChatGPT request or browser extension experiment was run, so popup runtime semantic capability is **not exercised**.

No external messages, approvals to unrelated work, environment dumps, daemon restarts or changes to the user's existing tmux sessions were performed. All cleanup targets the disposable session/server/bridge only.
