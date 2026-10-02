# Agent Office

Agent Office turns local coding-agent activity into a real-time, spatial office view. A FastAPI backend normalizes process, Git, filesystem, wrapper, and tool events; a React/PixiJS frontend projects those events into agent movement and animations.

## Quick start

```bash
uv sync
cd frontend && npm install && npm run build && cd ..
uv run agent-office
```

Open <http://127.0.0.1:8000>. For a standalone simulation, open <http://127.0.0.1:8000/?demo=true>.

Run a real agent through the wrapper:

```bash
uv run office-run codex --name Backend --role Backend --task "Implement API"
```

## Semantic agent definitions

Define stable names, roles and responsibilities in the server's office YAML `agents` list. Definitions are scoped to the primary project; additional `projects` may provide their own `agents`. See [the example configuration](config/semantic-agents.example.yaml).

```bash
AGENT_OFFICE_CONFIG=config/semantic-agents.example.yaml uv run agent-office
uv run office-run codex --definition tester --parent lead --task "Verify authentication changes"
```

The registered instance appears as Tester, with its definition responsibilities and parent ID in details. Role remains stable while task, state and executable change. Native/orchestrator events can provide authoritative overrides with `source=native`; project defaults outrank wrapper/API metadata. Existing unregistered agents retain fallback identity. Use `--id` when a caller owns instance identity; otherwise definition-based launches get distinct IDs.

## Native runtime capability probe (Phase 3A)

State Fidelity and Semantic Agent Model are complete. Phase 3A provides an opt-in diagnostic probe; the Phase 3B native adapter is not yet implemented. See the [capability matrix](docs/runtime-probe/CAPABILITY_MATRIX.md), [repeatable commands](docs/runtime-probe/CODEX.md) and [observed samples](docs/runtime-probe/SAMPLES.md).

```bash
uv run python -m backend.probe experiment --output-dir runtime/probe/run-01
```

This runs controlled real Codex turns in a disposable repository using existing runtime authentication. Logs are sanitized and ignored; the production API, domain states, identity resolver and frontend remain unchanged. For a loaded native TUI thread, `observe` attaches to its Unix WebSocket without answering requests or changing settings.

## DevRouter integration

When `office-run` is installed on PATH, DevRouter automatically uses it to wrap the Codex process inside each new project session. Start the shared Agent Office server, then run `devrouter` in the target repository; do not nest it as `office-run devrouter`. Use `devrouter --office` to require monitoring or `devrouter --no-office` to start Codex directly.

See the complete [HTML user guide](docs/agent-office-user-guide.html), also available at <http://127.0.0.1:8000/guide> while the server is running.

## Verification

```bash
uv run pytest
uv run ruff check backend main.py
cd frontend
npm test
npm run lint
npm run build
```
