# Repository Guidelines

## Project Structure & Module Organization

Agent Office has a Python 3.13/FastAPI backend and a React/TypeScript frontend. Domain models and transitions live in `backend/models.py` and `backend/state/`; integrations live in `backend/observer/` and `backend/adapters/`. HTTP/WebSocket routes are in `backend/api/`, with tests under `backend/tests/`.

Under `frontend/src/`, keep server communication in `api/`, shared state in `store/`, controls in `components/`, and PixiJS rendering in `office/`. Configuration belongs in `config/office.yaml`, scripts in `scripts/`, documentation in `docs/`, and generated logs in ignored `runtime/*.jsonl` files. `main.py` remains a thin launcher.

## Build, Test, and Development Commands

- `uv sync`: install locked backend and development dependencies.
- `cd frontend && npm run dev`: start Vite for frontend development.
- `cd frontend && npm run build && cd .. && uv run agent-office`: build the UI and serve the complete app at `http://127.0.0.1:8000`.
- `uv run office-run codex --name Backend`: launch and register a real coding agent.
- `uv run pytest` / `uv run ruff check backend main.py`: test and lint Python.
- `cd frontend && npm test && npm run lint`: test and lint TypeScript.

## Coding Style & Naming Conventions

Use four spaces, complete type hints, `snake_case` functions/modules, and `PascalCase` classes in Python. Keep blocking process or filesystem calls off the event loop, use Pydantic for API models, and avoid mutable module globals.

TypeScript uses strict mode. Name React components in `PascalCase` and utilities in `camelCase`. Avoid `any`; type agent models, events, and WebSocket messages. Keep domain transitions in the backend.

## Testing Guidelines

Use pytest for backend tests and Vitest for frontend behavior. Name Python tests `test_*.py`; colocate frontend tests as `*.test.ts` or `*.test.tsx`. Cover transitions, observer normalization, replay timing, store updates, and visual mappings. Run both test suites, linters, and the production build before submitting.

## Commit & Pull Request Guidelines

Use short, imperative subjects matching the history, such as `Add V1 live backend runtime`, and keep commits focused. Pull requests should summarize behavior changes, identify the affected milestone, list verification commands, link relevant issues, and include screenshots or recordings for visual changes.

## Security & Runtime Data

The API has no authentication and should remain bound to `127.0.0.1` unless protected by a trusted proxy. Never commit credentials, local repository details, generated frontend output, or `runtime/events.jsonl`.
