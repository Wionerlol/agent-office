"""Minimal diagnostic JSON-RPC transport, separate from the office runtime."""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection


class RpcClient:
    def __init__(
        self,
        command: list[str],
        receive: Callable[[dict[str, Any]], None],
        *,
        unix_socket: Path | None = None,
        collect_events: bool = True,
    ) -> None:
        self.command = command
        self.unix_socket = unix_socket
        self.collect_events = collect_events
        self.socket: ClientConnection | None = None
        self.receive = receive
        self.events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._requests: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._next_id = 0
        self.process: asyncio.subprocess.Process | None = None
        self._reader: asyncio.Task[None] | None = None

    async def __aenter__(self) -> Self:
        if self.unix_socket:
            from websockets.asyncio.client import unix_connect

            self.socket = await unix_connect(self.unix_socket, uri="ws://localhost/")
        else:
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                limit=4_194_304,
            )
        self._reader = asyncio.create_task(self._read())
        return self

    async def _read(self) -> None:
        stream = (
            self.socket
            if self.socket is not None
            else (self.process.stdout if self.process is not None else None)
        )
        assert stream is not None
        try:
            async for line in stream:
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError("not an object")
                except (ValueError, RecursionError):
                    self.receive({"type": "probe.malformed"})
                    continue
                if "method" in value:
                    self.receive(value)
                    if self.collect_events:
                        self.events.put_nowait(value)
                elif isinstance(value.get("id"), int) and value["id"] in self._requests:
                    future = self._requests[value["id"]]
                    if not future.done():
                        future.set_result(value)
        finally:
            for future in self._requests.values():
                if not future.done():
                    future.set_exception(ConnectionError("Native stream closed"))

    async def send(self, value: dict[str, Any]) -> None:
        if self.socket is not None:
            await self.socket.send(json.dumps(value))
            return
        assert self.process is not None and self.process.stdin is not None
        self.process.stdin.write((json.dumps(value) + "\n").encode())
        await self.process.stdin.drain()

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if self._reader is not None and self._reader.done():
            raise ConnectionError("Native stream closed")
        self._next_id += 1
        identifier = self._next_id
        future = asyncio.get_running_loop().create_future()
        self._requests[identifier] = future
        try:
            await self.send({"id": identifier, "method": method, "params": params})
            response = await asyncio.wait_for(future, timeout=30)
            if "error" in response:
                raise RuntimeError("Native RPC request rejected")
            if not isinstance(response.get("result"), dict):
                raise RuntimeError("Malformed native RPC response")
            return response["result"]
        finally:
            self._requests.pop(identifier, None)

    async def initialize(self) -> None:
        await self.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "agent_office_probe",
                    "title": "Runtime probe",
                    "version": "0.1",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        await self.send({"method": "initialized"})

    async def __aexit__(self, *_: object) -> None:
        if self.socket is not None:
            await self.socket.close()
            if self._reader:
                await asyncio.gather(self._reader, return_exceptions=True)
            return
        assert self.process is not None
        if self.process.stdin:
            self.process.stdin.close()
        try:
            await asyncio.wait_for(self.process.wait(), timeout=3)
        except TimeoutError:
            self.process.terminate()
            await self.process.wait()
        if self._reader:
            await asyncio.gather(self._reader, return_exceptions=True)
