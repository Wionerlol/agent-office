# Codex Entry Point

Before changing code, read these files in order:

1. `docs/VISION.md`
2. `docs/DECISIONS.md`
3. `docs/SPEC.md`
4. `docs/EXAMPLES.md`
5. `docs/ACCEPTANCE.md`
6. `docs/CONTEXT.md`
7. `docs/IMPLEMENTATION_PLAN.md`

Resolve conflicts using this priority:

1. the user's latest explicit decision;
2. `docs/DECISIONS.md`;
3. `docs/VISION.md`;
4. `docs/SPEC.md`;
5. implementation convenience.

Do not treat the older `agent-office-PROJECT.md` as authoritative when it conflicts with the files above. It remains useful historical context.

Project phases: State Fidelity COMPLETE; Semantic Agent Model COMPLETE; Phase 3A Native Runtime Capability Probe COMPLETE; Phase 3B Native Adapter v1 COMPLETE; Phase 3B v1.1 Integration Hardening COMPLETE. Read `docs/runtime-probe/` before proposing native normalization.

Implementation principles:
- preserve completed State Fidelity and Semantic Agent Model, including EventSource, status provenance/arbitration, and SemanticIdentityResolver;
- keep the opt-in probe isolated from live startup/API/frontend; capabilities require actual sanitized native evidence;
- keep Phase 3A diagnostic tooling separate; Phase 3B consumes only confirmed facts through OfficeRuntime, explicit bindings and existing arbitration;
- preserve native read-only scope, version gates, replay safety, and released-evidence fallback; do not add new top-level states;
- keep stable role/responsibilities distinct from task, state, and executable/tool;
- resolve semantic identity centrally from native metadata, project definitions, wrapper metadata, then process fallback;
- do not infer roles from tools/prompts or add an organization-tree UI;
- preserve the current frontend architecture unless a backend change requires a minimal diagnostic change;
- keep normalized domain logic provider-agnostic;
- prefer explicit runtime facts over heuristics;
- keep source precedence centralized and testable;
- preserve backward compatibility for existing API/WebSocket callers;
- do not broaden scope into visual redesign or a general event-sourcing platform;
- update `docs/DECISIONS.md` when you make a non-trivial implementation choice that is not already decided;
- do not declare completion until the acceptance criteria and verification commands pass.

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
