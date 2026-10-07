"""Observe one already-loaded Codex thread; never answer its server requests."""

import asyncio
from pathlib import Path
from typing import Any

from backend.probe.record import ProbeRecorder
from backend.probe.rpc import RpcClient


class ThreadScope:
    def __init__(self, thread_id: str, recorder: ProbeRecorder) -> None:
        self.threads = {thread_id}
        self.recorder = recorder

    def receive(self, value: dict[str, Any]) -> None:
        params = value.get("params")
        if not isinstance(params, dict):
            return
        thread = params.get("thread")
        if (
            isinstance(thread, dict)
            and isinstance(thread.get("parentThreadId"), str)
            and thread["parentThreadId"] in self.threads
        ):
            if isinstance(thread.get("id"), str):
                self.threads.add(thread["id"])
        identifier = params.get("threadId")
        if isinstance(thread, dict):
            identifier = thread.get("id")
        if not isinstance(identifier, str) or identifier not in self.threads:
            return
        item = params.get("item")
        if isinstance(item, dict) and isinstance(item.get("agentThreadId"), str):
            self.threads.add(item["agentThreadId"])
        self.recorder.record(value)


async def observe_thread(
    socket: Path,
    thread_id: str,
    workspace: Path,
    recorder: ProbeRecorder,
    duration: float,
) -> None:
    scope = ThreadScope(thread_id, recorder)
    async with RpcClient([], scope.receive, unix_socket=socket, collect_events=False) as rpc:
        await rpc.initialize()
        metadata = await rpc.request("thread/read", {"threadId": thread_id, "includeTurns": False})
        thread = metadata["thread"]
        actual_root = await asyncio.to_thread(Path(thread["cwd"]).resolve)
        expected_root = await asyncio.to_thread(workspace.resolve)
        if actual_root != expected_root:
            raise ValueError("Selected thread is outside the requested workspace")
        if thread["status"]["type"] not in {"active", "idle"}:
            raise ValueError(
                "Observe only an already-loaded thread; do not load historical sessions"
            )
        # On these installed versions resume subscribes the connection. No settings/input override.
        resumed = await rpc.request("thread/resume", {"threadId": thread_id, "excludeTurns": True})
        recorder.record(
            {
                "method": "probe.subscription.response",
                "params": {
                    "thread": resumed["thread"],
                },
            }
        )
        observed = {thread_id}
        deadline = asyncio.get_running_loop().time() + duration
        while asyncio.get_running_loop().time() < deadline:
            for child in scope.threads - observed:
                metadata = await rpc.request(
                    "thread/read", {"threadId": child, "includeTurns": False}
                )
                recorder.record({"method": "probe.child.metadata", "params": metadata})
                observed.add(child)
            await asyncio.sleep(min(0.25, max(0, deadline - asyncio.get_running_loop().time())))
        # Close only this diagnostic WebSocket, leaving the TUI and shared daemon running.
