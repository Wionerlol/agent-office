# Minimal observed samples

These are selected, sanitized records from actual Codex runs on 2026-10-02, not manufactured provider fixtures. Envelopes, receipt timestamps and sequence numbers are from the probe; raw_type and payload discriminators retain native spelling. IDs are stable pseudonyms. Content/diffs/arguments are redacted. Gaps in sequence numbers mean deliberately omitted records. probe.* methods identify diagnostic RPC snapshots, not native notification names. Some earlier captures predate the additional provider_sequence envelope field; this does not create a native timestamp/ordinal where none existed.

## S1 Turn and idle

Standalone app-server scenario A. Active/turn lifecycle is confirmed, but active alone is not a THINKING fact.

```json
{"sequence":10,"timestamp":"2026-10-02T10:06:16.371017+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"turn/started","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","turn":{"id":"id-bce4cf3c4f2f5f0080df","status":"inProgress","error":null}}}
{"sequence":72,"timestamp":"2026-10-02T10:07:14.682087+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"thread/status/changed","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","status":{"type":"idle"}}}
{"sequence":73,"timestamp":"2026-10-02T10:07:14.682194+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"turn/completed","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","turn":{"id":"id-bce4cf3c4f2f5f0080df","status":"completed","error":null,"durationMs":55084}}}
```

## S2 Reasoning

Scenario D emitted reasoning items; ordinary A did not. No reasoning text is retained.

```json
{"sequence":191,"timestamp":"2026-10-02T10:07:44.983316+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"reasoning","id":"id-17158a53250ebc8eff6b","summary":"[redacted]","content":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-0e9f05cdfe201dc77324"}}
{"sequence":192,"timestamp":"2026-10-02T10:07:45.393979+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"reasoning","id":"id-17158a53250ebc8eff6b","summary":"[redacted]","content":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-0e9f05cdfe201dc77324"}}
```

## S3 File edit

Scenario B applied a patch to calc.py. The controlled module was independently checked with AST parsing and returned 42; subsequent actual pytest succeeded. No watcher supplied this evidence.

```json
{"sequence":96,"timestamp":"2026-10-02T10:07:21.368284+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"fileChange","id":"id-97c3985f0efaf91e14a8","changes":[{"path":"calc.py","kind":{"type":"update"},"diff":"[redacted]"}],"status":"inProgress"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-ebc3c6a173ad6fb45893"}}
{"sequence":97,"timestamp":"2026-10-02T10:07:21.415075+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"fileChange","id":"id-97c3985f0efaf91e14a8","changes":[{"path":"calc.py","kind":{"type":"update"},"diff":"[redacted]"}],"status":"completed"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-ebc3c6a173ad6fb45893"}}
```

## S4 Tools

Actual rg, printf and pytest. commandActions/executable hints describe observed commands; they do not add native TESTING/SEARCHING AgentState values. Native annotation type=search is present for rg. The same item IDs correlate starts and completions.

```json
{"sequence":147,"timestamp":"2026-10-02T10:07:31.386446+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-3499942d96c97fc66c59","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-37f4ca87daf7cfc6992c","source":"unifiedExecStartup","status":"inProgress","commandActions":[{"type":"search","command":{"redacted":true,"executable_tokens":["rg"]},"path":"calc.py"}],"aggregatedOutput":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
{"sequence":148,"timestamp":"2026-10-02T10:07:31.391455+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-3499942d96c97fc66c59","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-37f4ca87daf7cfc6992c","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"search","command":{"redacted":true,"executable_tokens":["rg"]},"path":"calc.py"}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":0},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
```

```json
{"sequence":149,"timestamp":"2026-10-02T10:07:31.466461+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-e93d6b8c37dd1be593a0","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-17e7eaad7f40d2f2fb32","source":"unifiedExecStartup","status":"inProgress","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["printf"]}}],"aggregatedOutput":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
{"sequence":150,"timestamp":"2026-10-02T10:07:31.466736+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-e93d6b8c37dd1be593a0","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-17e7eaad7f40d2f2fb32","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["printf"]}}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":0},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
```

```json
{"sequence":151,"timestamp":"2026-10-02T10:07:31.624433+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-d1b22126cb442a31b34a","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-5069efb90c5dcc14ff24","source":"unifiedExecStartup","status":"inProgress","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["pytest","python3"]}}],"aggregatedOutput":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
{"sequence":155,"timestamp":"2026-10-02T10:07:32.128009+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-d1b22126cb442a31b34a","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-5069efb90c5dcc14ff24","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["pytest","python3"]}}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":488},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-12aedcb003afbb441d21"}}
```

## S5 User input required

A real unresolved contract (43 or 44) triggered a native request in Plan mode. The direct harness waited before answering. This is distinct from idle.

```json
{"sequence":185,"timestamp":"2026-10-02T10:07:40.917950+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"thread/status/changed","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","status":{"type":"active","activeFlags":["waitingOnUserInput"]}}}
{"sequence":186,"timestamp":"2026-10-02T10:07:40.918240+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/tool/requestUserInput","request_id":"id-5feceb66ffc86f38d952","source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-0e9f05cdfe201dc77324","itemId":"id-554018606912d39ac1fa","questions":[{"id":"id-1989eae3cf5a8315376e","header":"[redacted]","question":"[redacted]","isOther":true,"isSecret":false,"options":[{"label":"[redacted]","description":"[redacted]"},{"label":"[redacted]","description":"[redacted]"}]}]}}
{"sequence":187,"timestamp":"2026-10-02T10:07:42.919679+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"serverRequest/resolved","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-5e35c21f2f6eb7d86b82","requestId":"id-5feceb66ffc86f38d952"}}
```

On the real DevRouter TUI, a passive reconnect replayed the still-pending request, and the original TUI supplied the answer. Request IDs correlate resolution; replay must not manufacture a new wait.

```json
{"sequence":3,"timestamp":"2026-10-02T10:01:54.132066+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"item/tool/requestUserInput","request_id":"id-5feceb66ffc86f38d952","source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-c44c428b0764cf580a70","itemId":"id-8fd19aaf79e0ec58e932","questions":[{"id":"id-0f08f8eb07c7058be44e","header":"[redacted]","question":"[redacted]","isOther":true,"isSecret":false,"options":[{"label":"[redacted]","description":"[redacted]"},{"label":"[redacted]","description":"[redacted]"}]}]}}
{"sequence":4,"timestamp":"2026-10-02T10:03:15.493612+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"serverRequest/resolved","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd","requestId":"id-5feceb66ffc86f38d952"}}
```

## S6 Subagents and delegation

Real DevRouter/shared-daemon delegation. The native child ID in activity matches metadata; parentThreadId matches the root thread. agentRole is null despite requesting review. The wait call confirms waiting, but its receiverThreadIds/agentsStates were empty. Nickname is not a stable responsibility.

```json
{"sequence":136,"timestamp":"2026-10-02T10:08:17.493594+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"subAgentActivity","id":"id-cc919276682c93c8ebf5","kind":"started","agentThreadId":"id-4ae8b575f6c2ca3f719a"},"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-6d3a9e59b4032d38e59b"}}
{"sequence":142,"timestamp":"2026-10-02T10:08:17.668235+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-4ae8b575f6c2ca3f719a","raw_type":"probe.child.metadata","request_id":null,"source":"codex-app-server","payload":{"thread":{"id":"id-4ae8b575f6c2ca3f719a","sessionId":"id-cfcd659a1a7485391ccd","parentThreadId":"id-cfcd659a1a7485391ccd","preview":"[redacted]","createdAt":1790935697,"updatedAt":1790935697,"status":{"type":"active","activeFlags":[]},"path":"[outside-workspace]","cwd":".","cliVersion":"0.160.0","originator":"codex-tui","source":{"subAgent":{"thread_spawn":{"parent_thread_id":"id-cfcd659a1a7485391ccd","depth":1,"agent_nickname":"Averroes","agent_role":null}}},"canAcceptDirectInput":false,"agentNickname":"Averroes","agentRole":null,"name":"[redacted]"}}}
{"sequence":144,"timestamp":"2026-10-02T10:08:21.065957+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"collabAgentToolCall","id":"id-517277607de4d7904b5d","tool":"wait","status":"inProgress","senderThreadId":"id-cfcd659a1a7485391ccd","receiverThreadIds":[],"prompt":"[redacted]","agentsStates":{}},"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-6d3a9e59b4032d38e59b"}}
{"sequence":188,"timestamp":"2026-10-02T10:08:29.818036+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"subAgentActivity","id":"id-fb19e41429fe893d1ccb","kind":"completed","agentThreadId":"id-4ae8b575f6c2ca3f719a"},"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-6d3a9e59b4032d38e59b"}}
{"sequence":190,"timestamp":"2026-10-02T10:08:29.822933+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"collabAgentToolCall","id":"id-517277607de4d7904b5d","tool":"wait","status":"completed","senderThreadId":"id-cfcd659a1a7485391ccd","receiverThreadIds":[],"prompt":"[redacted]","agentsStates":{}},"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-6d3a9e59b4032d38e59b"}}
```

Direct standalone metadata independently exposes parentage and a generated nickname, with no stable role:

```json
{"sequence":460,"timestamp":"2026-10-02T10:08:16.379999+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-9f6d7ea05f6399218d83","raw_type":"probe.child.metadata","request_id":null,"source":"codex-app-server","payload":{"thread":{"id":"id-9f6d7ea05f6399218d83","sessionId":"id-5e35c21f2f6eb7d86b82","parentThreadId":"id-5e35c21f2f6eb7d86b82","preview":"[redacted]","createdAt":1790935681,"updatedAt":1790935690,"status":{"type":"idle"},"path":"[outside-workspace]","cwd":".","cliVersion":"0.159.3","originator":"agent_office_probe","source":{"subAgent":{"thread_spawn":{"parent_thread_id":"id-5e35c21f2f6eb7d86b82","depth":1,"agent_nickname":"Mendel","agent_role":null}}},"canAcceptDirectInput":false,"agentNickname":"Mendel","agentRole":null,"name":"[redacted]"}}}
```

## S7 Plans and conversation context

Plan item and TUI goal-cleared notification exist. Neither proves an Agent.task assignment update; text is not classified.

```json
{"sequence":216,"timestamp":"2026-10-02T10:07:49.413705+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-5e35c21f2f6eb7d86b82","raw_type":"item/started","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"plan","id":"id-824438fca0a9bbdb216a","text":"[redacted]"},"threadId":"id-5e35c21f2f6eb7d86b82","turnId":"id-0e9f05cdfe201dc77324"}}
{"sequence":2,"timestamp":"2026-10-02T10:06:11.509428+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"thread/goal/cleared","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd"}}
```

## S8 ToolObserver comparison

Under direct standalone app-server, unchanged ToolObserver produced process-derived search/test events. Under the real wrapped TUI PID, 45 seconds of 10 ms scanning produced zero tool events while rg/printf/pytest completed. Native paginated history of that exact latest turn independently contains three completed commands with exitCode=0. These snapshots are not live start/finish notifications, and zero PID observations is a demonstrated visibility limit, not passing native verification.

```json
{"sequence":4,"timestamp":"2026-10-02T10:18:09.399648+00:00","provider_timestamp":null,"provider_sequence":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"probe.history.item","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-45783a2c79e6bee7e012","item":{"type":"commandExecution","id":"id-4b1a72a1243ec983bb86","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-eae0433b15dff383cae2","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"search","command":{"redacted":true,"executable_tokens":["rg"]},"path":"calc.py"}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":0}}}
{"sequence":5,"timestamp":"2026-10-02T10:18:09.399934+00:00","provider_timestamp":null,"provider_sequence":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"probe.history.item","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-45783a2c79e6bee7e012","item":{"type":"commandExecution","id":"id-de0ea6114cb59b2689da","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-9ae4e271aa8c5f36a003","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["printf"]}}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":0}}}
{"sequence":6,"timestamp":"2026-10-02T10:18:09.400127+00:00","provider_timestamp":null,"provider_sequence":null,"provider":"codex","session_id":"id-cfcd659a1a7485391ccd","raw_type":"probe.history.item","request_id":null,"source":"codex-app-server","payload":{"threadId":"id-cfcd659a1a7485391ccd","turnId":"id-45783a2c79e6bee7e012","item":{"type":"commandExecution","id":"id-ed914720c13069dff690","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-54e0e28893d91b045bff","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"unknown","command":{"redacted":true,"executable_tokens":["pytest","python"]}}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":463}}}
```

## S9 Structured file-read annotation

An E child shell read was annotated commandActions.type=read with path=calc.py. Other cat commands were annotated unknown. This confirms a structured command annotation, not universal native file-access instrumentation.

```json
{"sequence":367,"timestamp":"2026-10-02T10:08:07.583082+00:00","provider_timestamp":null,"provider":"codex","session_id":"id-9f6d7ea05f6399218d83","raw_type":"item/completed","request_id":null,"source":"codex-app-server","payload":{"item":{"type":"commandExecution","id":"id-e0d87116723d59696d64","command":{"redacted":true,"executable_tokens":["bash"]},"cwd":".","processId":"id-935fece5fda4f757b642","source":"unifiedExecStartup","status":"completed","commandActions":[{"type":"read","command":{"redacted":true,"executable_tokens":["cat"]},"name":"[redacted]","path":"calc.py"}],"aggregatedOutput":"[redacted]","exitCode":0,"durationMs":0},"threadId":"id-9f6d7ea05f6399218d83","turnId":"id-59c2edb70d703363f2db"}}
```
