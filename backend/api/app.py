import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import OfficeSettings, Settings
from backend.models import Agent, AgentEvent, CodexUsage, ProjectInfo
from backend.observer.codex_usage import CodexUsageMonitor
from backend.observer.git import GitObserver
from backend.observer.manager import ObserverManager
from backend.runtime.office import OfficeRuntime
from backend.state.engine import StateTransitionError


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    runtime = OfficeRuntime()
    observer = ObserverManager(runtime, settings.observer)
    usage_monitor = CodexUsageMonitor.from_environment()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.observer.enabled:
            observer.start()
        yield
        await observer.stop()

    app = FastAPI(title="Agent Office", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.runtime = runtime
    app.state.observer = observer
    app.state.usage_monitor = usage_monitor
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{settings.frontend.port}",
            f"http://127.0.0.1:{settings.frontend.port}",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/agents")
    async def agents() -> list[Agent]:
        return runtime.registry.all()

    @app.get("/api/agents/{agent_id}")
    async def agent(agent_id: str) -> Agent:
        try:
            return runtime.registry.get(agent_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/project")
    async def project() -> ProjectInfo:
        snapshot = await asyncio.to_thread(GitObserver(settings.project.path).snapshot)
        return ProjectInfo(
            name=settings.project.name,
            path=str(settings.project.path),
            branch=snapshot.branch,
        )

    @app.get("/api/projects")
    async def projects() -> list[ProjectInfo]:
        configured = settings.projects or [settings.project]
        return [ProjectInfo(name=item.name, path=str(item.path)) for item in configured]

    @app.get("/api/config")
    async def public_config() -> OfficeSettings:
        return settings.office

    @app.get("/api/codex-usage")
    async def codex_usage() -> CodexUsage:
        return await asyncio.to_thread(usage_monitor.snapshot)

    @app.post("/api/events")
    async def receive_event(event: AgentEvent) -> dict[str, Any]:
        try:
            return await runtime.apply(event)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except StateTransitionError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "snapshot",
                "agents": [agent.model_dump(mode="json") for agent in runtime.registry.all()],
            }
        )
        queue = runtime.bus.subscribe()
        try:
            while True:
                event_task = asyncio.create_task(queue.get())
                client_task = asyncio.create_task(websocket.receive())
                done, pending = await asyncio.wait(
                    {event_task, client_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                if client_task in done:
                    client_message = client_task.result()
                    if client_message["type"] == "websocket.disconnect":
                        break
                if event_task in done:
                    await websocket.send_json(event_task.result())
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            runtime.bus.unsubscribe(queue)

    dist = Path(__file__).parents[2] / "frontend" / "dist"
    guide = Path(__file__).parents[2] / "docs" / "agent-office-user-guide.html"
    if guide.exists():

        @app.get("/guide", include_in_schema=False)
        async def user_guide() -> FileResponse:
            return FileResponse(guide)

    if dist.exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/", include_in_schema=False)
        async def frontend() -> FileResponse:
            return FileResponse(dist / "index.html")

    return app
