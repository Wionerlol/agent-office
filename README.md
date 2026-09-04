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
