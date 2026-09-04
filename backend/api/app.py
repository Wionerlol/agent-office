import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import Settings
from backend.models import AgentEvent, ProjectInfo
from backend.observer.manager import ObserverManager
from backend.runtime.office import OfficeRuntime
from backend.runtime.storage import EventStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.load()
    runtime = OfficeRuntime(EventStorage(settings.runtime_path))
    observer = ObserverManager(runtime, settings.observer)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await runtime.restore()
        if settings.observer.enabled:
            observer.start()
        yield
        await observer.stop()

    app = FastAPI(title="Agent Office", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.runtime = runtime
    app.state.observer = observer
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[f"http://localhost:{settings.frontend.port}", f"http://127.0.0.1:{settings.frontend.port}"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/agents")
    async def agents():
        return runtime.registry.all()

    @app.get("/api/agents/{agent_id}")
    async def agent(agent_id: str):
        try:
            return runtime.registry.get(agent_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/project")
    async def project() -> ProjectInfo:
        branch = None
        head = settings.project.path / ".git" / "HEAD"
        if head.exists():
            content = head.read_text(encoding="utf-8").strip()
            branch = content.rsplit("/", 1)[-1] if content.startswith("ref:") else content[:12]
        return ProjectInfo(
            name=settings.project.name,
            path=str(settings.project.path),
            branch=branch,
        )

    @app.get("/api/projects")
    async def projects() -> list[dict[str, str]]:
        configured = settings.projects or [settings.project]
        return [{"name": item.name, "path": str(item.path)} for item in configured]

    @app.post("/api/events")
    async def receive_event(event: AgentEvent):
        try:
            return await runtime.apply(event)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/history")
    async def history(
        agent_id: str | None = None,
        limit: int = Query(default=1000, ge=1, le=10_000),
    ) -> list[AgentEvent]:
        events = runtime.storage.read()
        if agent_id:
            events = [event for event in events if event.agent_id == agent_id]
        return events[-limit:]

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
                message = await queue.get()
                await websocket.send_json(message)
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        finally:
            runtime.bus.unsubscribe(queue)

    dist = Path(__file__).parents[2] / "frontend" / "dist"
    if dist.exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=assets), name="assets")

        @app.get("/", include_in_schema=False)
        async def frontend() -> FileResponse:
            return FileResponse(dist / "index.html")

    return app
