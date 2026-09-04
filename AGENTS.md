# Repository Guidelines

## Project Structure & Module Organization

This repository is an early-stage Python 3.13 project managed with `uv`. The current executable is `main.py`; dependency and interpreter metadata live in `pyproject.toml`, `uv.lock`, and `.python-version`. The product plan is documented in `agent-office-PROJECT.md`.

Follow the planned separation as the application grows: place FastAPI services, observers, adapters, state logic, and backend tests under `backend/`; put the React/TypeScript application in `frontend/src/`; store static configuration in `config/`, helper commands in `scripts/`, and generated event data in `runtime/`. Keep business state transitions out of UI animation components.

## Build, Test, and Development Commands

- `uv sync`: create or update the local virtual environment from `uv.lock`.
- `uv run python main.py`: run the current placeholder application.
- `uv run pytest`: run backend tests once the test suite is introduced.
- `cd frontend && npm install`: install frontend dependencies after the Vite app is scaffolded.
- `cd frontend && npm run dev`: start the planned frontend development server.
- `cd frontend && npm run build`: type-check and build the frontend before submitting changes.

Commit updates to `uv.lock` or the frontend lockfile whenever dependencies change.

## Coding Style & Naming Conventions

Use four spaces, type hints, `snake_case` functions/modules, and `PascalCase` classes in Python. Prefer small modules, `async`/`await` for I/O, Pydantic for API models, and dataclasses where appropriate. Avoid global mutable state and oversized entry points.

TypeScript must use strict mode. Name React components in `PascalCase` (for example, `AgentSprite.tsx`) and other modules in descriptive camelCase or established project patterns. Avoid `any`; define interfaces or types for core models and WebSocket events.

## Testing Guidelines

Use pytest for backend tests and Vitest for frontend state logic. Name Python tests `test_*.py` and colocate frontend tests as `*.test.ts` or `*.test.tsx`. Prioritize state-engine transitions, registry behavior, event serialization, adapter normalization, reducers, and state-to-visual-action mappings. Every completed phase should pass tests, linting, and production builds.

## Commit & Pull Request Guidelines

History currently contains only an initialization commit, so no mature convention exists. Use short, imperative subjects such as `Add agent state registry`, and keep each commit focused. Pull requests should state the milestone addressed, summarize behavior changes, list verification commands, link relevant issues, and include screenshots or recordings for visual changes. Do not advance beyond the current project phase without explicit agreement.
