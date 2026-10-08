# Fresh-session native-thread correlation

## Outcome: UPSTREAM / RUNTIME LIMITATION

Investigation completed on 2026-10-08. No deterministic launcher-owned identity was exposed by the exercised fresh Codex TUI paths. This is an investigation-only result, not Phase 3B v1.2. Keep explicit UUID binding and all v1/v1.1 behavior. Stop runtime infrastructure work and begin Phase 4 in a separate task.

This conclusion covers the installed surfaces and experiments below, not every future Codex version or execution mode. A generated thread UUID identifies the native thread; it does not identify which Office launcher owns it. No thread was bound by repository, arrival order, timestamps, PID, terminal text, title or prompt similarity.

## Versions and environment boundary

- Installed PATH CLI: **0.160.0**. Shared daemon: **0.161.0**.
- Generated experimental schemas inspected from both installed binaries; CLI/help/resume/agents/app-server invocation surfaces inspected locally.
- Fresh PATH CLI launches stopped before thread creation at a shared-feature incompatibility dialog (`api_key_model_discovery`). They are **not** passing fresh-session evidence. The daemon was not restarted and its feature settings were not changed.
- Successful experiments used the existing daemon-package **0.161.0 CLI**, selected through an experiment-local PATH, with the same running **0.161.0 daemon**. This did not upgrade/replace PATH Codex, alter user sandbox/feature configuration or widen production profiles.
- Disposable committed repository; isolated loopback Office server; independent tmux sockets and DevRouter homes. The fixture folder trust dialog was accepted for the owned repository. No model turn, prompt injection, approval, request answer or thread/start RPC was needed.

## Actual experiments

The final successful run recorded **19 content-denying structural records**: five thread/started notifications, nine metadata-only reads during A/B/C, and five reads after closing/reopening only the diagnostic observer connection. Arrival timestamps are UTC receipt times, not execution or ownership evidence.

**A — direct fresh launch:** `office-run codex --id direct-a` with no resume UUID or inherited native UUID. A random AGENT_OFFICE_CORRELATION_ID was supplied to the launcher environment. After normal TUI startup, thread/started was received before any user/model turn; thread/read exposed the same native identity. The controlled nonce was absent from the complete in-memory Thread object. Nothing was automatically bound.

**B — concurrent direct launches:** two additional distinct Office IDs were launched close together in the **same repository**, each with a different controlled nonce. As an additional failed candidate, each also received its nonce through the binary-discovered CODEX_INTERNAL_ORIGINATOR_OVERRIDE environment variable. Two new thread/started events arrived 144 ms apart. Both had source=vscode, originator=codex-tui and different generated thread/session IDs. Neither nonce appeared anywhere in either Thread object. These IDs cannot be assigned to the two Office IDs from structured evidence; there are two valid permutations. Event order is not a solution.

**C — concurrent actual DevRouter launches:** two installed `devrouter --office` CLIs used separate disposable homes/tmux servers but the **same repository**. Each launched its actual office-run → Codex TUI path with its own controlled correlation/originator-override nonce. Two additional thread/started notifications arrived 98 ms apart. Both had the same generic source/originator and no controlled nonce. Both TUIs reached their empty composer; no request/turn was sent. DevRouter does not add a native launch callback or expose a returned native UUID in its inspected launch code.

DevRouter has a separate Office identity limitation: `terminal.commands` derives `project-<repository hash>` from the repository alone. Different homes isolate tmux servers but still produce the same Office ID. Thus this experiment exercised two real native sessions, **not two independently registered DevRouter Office identities**. Final diagnostics showed three direct IDs plus one shared DevRouter ID, health=unbound and zero bindings. A wrapper event-drop warning occurred in one DevRouter terminal; neither that warning nor the duplicate Office ID prevented the two native thread creation events. Do not claim full concurrent DevRouter Office identity support. The external package was not modified.

**D — reconnect:** close/reopen only the diagnostic Unix WebSocket; keep all five TUIs running. All five metadata reads retained their native IDs and generic classifications, with no nonce after reconnect. This confirms native-thread persistence across observer reconnect, **not reconstructible Office ownership**. Production bindings remained empty. No long-running recovery/soak work was added.

## Decision matrix

CONFIRMED requires actual deterministic launcher → thread evidence. PARTIAL means a real structural component exists but the ownership contract is missing. UNAVAILABLE is scoped to this runtime/path; UNKNOWN means not exercised. UNSUITABLE includes prohibited heuristics regardless of apparent success.

| Candidate | Direct Codex | DevRouter | Distinguishes concurrent same-repo launches | Persistent | Safe | Conclusion |
| --- | --- | --- | --- | --- | --- | --- |
| cwd/repository | Present | Present | No | Yes | Validation only | UNSUITABLE |
| PID/PPID/process proximity | OS facts only; no native ownership field | tmux/wrapper adds processes | No native contract | Process lifetime only | Not identity | UNSUITABLE; not used for matching |
| Newest/only thread, timing | Creation/receipt timestamps exist | Same | No | Irrelevant | Not identity | UNSUITABLE; never tested as binding |
| Title, prompt/task/name similarity | Not an ownership contract | Same | No | Irrelevant | Content/heuristic risk | UNSUITABLE; no content retained |
| AGENT_OFFICE_CORRELATION_ID | No nonce match in A/B metadata | No nonce match in C metadata | No | Not exposed | Harmless controlled experiment | UNAVAILABLE in exercised Thread surface |
| CODEX_INTERNAL_ORIGINATOR_OVERRIDE | B still reports codex-tui | C still reports codex-tui | No | No controlled value exposed | Internal/undocumented; not a public contract | UNSUITABLE for production; failed runtime candidate |
| source/originator | vscode / codex-tui | vscode / codex-tui | No | Survives reconnect | Safe generic labels | UNSUITABLE as launcher identity |
| clientInfo / initialize | Schema has name/title/version; normal TUI CLI has no client-ID option | No additional launch contract | Not established | Connection metadata, not an Office binding | Read-only inspection safe | PARTIAL; own observer clientInfo cannot identify another client |
| thread/started | Actual Thread object received before first turn | Actual event received | Native IDs differ, Office owners absent | Thread metadata survives reconnect | Safe when content projected away | PARTIAL; event exists, causal Office field absent |
| sessionId / thread ID / parentThreadId | Root sessionId equals thread ID; no parent | Same | Native uniqueness only | Survives reconnect | Explicit UUID remains valid | PARTIAL; IDs originate in Codex, not the launcher |
| Fresh CLI --session-id/--thread-id/--metadata/--client-id/--tag | No such option in installed fresh CLI help | Passes Codex args unchanged | No supported mechanism | N/A | No undocumented flag invented | UNAVAILABLE in inspected CLI |
| Thread extra/environments/threadSource | Schema fields exist, no experiment nonce | Same | No demonstrated contract | Unknown for custom payloads | Do not dump environments/config | UNKNOWN for custom writes; no fresh CLI carrier found |
| app-server thread/start response | Explicit caller receives exact native ID (prior Phase 3B evidence) | DevRouter currently starts TUI instead | Yes for a creating RPC caller; not ordinary fresh TUI | Known-ID resume remains explicit | Requires launcher-owned creation; not read-only | PARTIAL alternative with architectural tradeoff; not implemented/exercised here |
| Hook notifications / configured callbacks | Schema exposes threadId and hook run metadata | No installed router callback | No demonstrated inherited nonce/ownership | Not established | Config/trust/side effects require separate review | UNKNOWN; no hooks/configuration installed for this investigation |
| Dedicated endpoint/proxy per launcher | Not the normal shared-daemon path | Would change router launch transport | Potentially, untested | Unknown | Alters transport/ownership boundary | UNKNOWN; no proxy/controller added |
| Existing literal resume/supplied UUID | v1.1 confirmed explicit handshake | v1.1 confirmed explicit resume | Yes with distinct Office IDs and supplied UUIDs | Runtime-local binding survives reconnect | Existing contract | CONFIRMED explicit binding, **not fresh discovery** |

ThreadStartParams contains config/projectId/threadSource/sessionStartSource/environments, but no caller-supplied thread UUID. InitializeParams contains clientInfo/capabilities. ThreadStartedNotification contains a Thread, not an Office launch ID or client connection correlation. The generated notification union has thread/started and lifecycle/status events, but no separate TUI/client-attached event carrying an Office token. ThreadExtra is implementation-specific, not a demonstrated metadata carrier. Hook notifications similarly do not establish launcher ownership. Schema presence alone is not runtime capability evidence.

Creating a thread through app-server would give that RPC caller its exact ID without necessarily starting a turn. It is nevertheless a write/control operation, not passive observation. Prior work also found newly created empty threads may lack a resumable rollout. Seamless empty-thread creation → ordinary TUI attach was **not established here**; no turns were injected to make it work. Keep that possible future upstream/integration design distinct from a supported fresh launch contract.

## Minimal sanitized evidence

These are projections of actual events from the final run. Native IDs are pseudonymous and no launch-to-thread pairing is implied within each concurrent pair. Field inventories and nonce-present booleans were computed before persistence; source/prompt/preview/turn content, UUIDs, absolute paths and nonce values are omitted.

```jsonl
{"received_at":"2026-10-08T05:48:26.906288+00:00","method":"thread/started","thread":"A-native","source":"vscode","originator":"codex-tui","session_equals_thread":true,"nonce_present":false}
{"received_at":"2026-10-08T05:48:41.429869+00:00","method":"thread/started","thread":"B-native-1","source":"vscode","originator":"codex-tui","session_equals_thread":true,"nonce_present":false}
{"received_at":"2026-10-08T05:48:41.573078+00:00","method":"thread/started","thread":"B-native-2","source":"vscode","originator":"codex-tui","session_equals_thread":true,"nonce_present":false}
{"received_at":"2026-10-08T05:49:03.090832+00:00","method":"thread/started","thread":"C-native-1","source":"vscode","originator":"codex-tui","session_equals_thread":true,"nonce_present":false}
{"received_at":"2026-10-08T05:49:03.188487+00:00","method":"thread/started","thread":"C-native-2","source":"vscode","originator":"codex-tui","session_equals_thread":true,"nonce_present":false}
```

## Reproduction and privacy

Use an owned committed repository, a loopback Office configuration with native integration enabled, and independent owned terminal sessions. Generate random nonces only in those launcher environments. Connect a diagnostic client to the existing daemon and initialize without changing settings. Record only fixture thread/started events and metadata-only reads, project identifiers/paths away, and test exact controlled-nonce presence in memory. A diagnostic repository filter scopes the **experiment dataset only**, never production identity. Do not retain other threads' metadata. For the concurrent cases launch two direct wrappers with different Office IDs, then two actual DevRouter CLIs with separate homes; retain their known duplicate-ID limitation. Close/reopen just the observer and repeat structural reads.

Do not change shared features to overcome the 0.160.0 fresh-start incompatibility. The successful run used the already-installed matching daemon CLI via an isolated PATH. Generated schemas, disposable scripts and filtered records remain ignored under runtime/probe. Cleanup closed only owned tmux servers, router/bridge processes, observer and loopback Office server. No raw prompts, reasoning, tool output, patches, auth state or environment dumps were written.

## Remaining operator workflow

See [NATIVE_RUNTIME.md](../NATIVE_RUNTIME.md#fresh-session-operator-workflow). A fresh session stays on existing fallbacks until the operator supplies its **exact** native UUID; CLI bind removes raw HTTP/JSON, not UUID discovery. If exact ownership is unavailable, remain unbound. Future automatic support needs an upstream structured launcher token/callback or a separately approved thread-creation/attach contract, with same-repository concurrency evidence.
