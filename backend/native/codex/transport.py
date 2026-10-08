"""Read-only local daemon transport; no production dependency on diagnostic logging."""

import asyncio
import json
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, Self

from websockets.asyncio.client import ClientConnection, unix_connect

from backend.native.codex.protocol import (
    NativeConnectionFailure,
    NativeReadFailure,
    NativeUnavailable,
    UnsupportedProtocol,
    require_version,
)


async def discover(codex: str) -> tuple[str, Path]:
    process = await asyncio.create_subprocess_exec(
        codex,
        "app-server",
        "daemon",
        "version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        limit=65536,
    )
    try:
        async with asyncio.timeout(5):
            output, _ = await process.communicate()
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()
    if process.returncode or len(output) > 65536:
        raise NativeUnavailable("Native daemon version unavailable")
    value = json.loads(output)
    version = value.get("appServerVersion")
    path = value.get("socketPath")
    if (
        value.get("status") != "running"
        or not isinstance(version, str)
        or not re.fullmatch(r"\d+\.\d+\.\d+", version)
        or not isinstance(path, str)
    ):
        raise NativeUnavailable("No running local Codex daemon")
    return version, Path(path)


class ReadOnlyClient:
    def __init__(
        self,
        path: Path,
        version: str,
        receive: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        self.path = path
        self.version = version
        self.profile = None
        self.receive = receive
        self.socket: ClientConnection | None = None
        self.reader: asyncio.Task[None] | None = None
        self.pending: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self.counter = 0

    async def __aenter__(self) -> Self:
        self.profile = require_version(self.version)
        self.socket = await unix_connect(
            self.path,
            uri="ws://localhost/",
            open_timeout=5,
            max_size=4_194_304,
            max_queue=16,
        )
        self.reader = asyncio.create_task(self._read())
        try:
            result = await self.request(
                "initialize",
                {
                    "clientInfo": {"name": "agent_office_native", "version": "0.1"},
                    "capabilities": {"experimentalApi": True},
                },
            )
            match = re.search(
                r"(?:^|\s)codex-tui/(\d+\.\d+\.\d+)(?:\s|$)", str(result.get("userAgent", ""))
            )
            if not match or match[1] != self.version:
                raise UnsupportedProtocol("Daemon handshake version mismatch")
            await self.socket.send(json.dumps({"method": "initialized"}))
        except BaseException:
            await self.__aexit__()
            raise
        return self

    async def _read(self) -> None:
        assert self.socket is not None
        try:
            async for line in self.socket:
                try:
                    value = json.loads(line)
                except (ValueError, RecursionError):
                    raise NativeUnavailable("Malformed native stream") from None
                if not isinstance(value, dict):
                    raise NativeUnavailable("Malformed native envelope")
                if "method" in value:
                    await self.receive(value)
                elif type(value.get("id")) is int and value["id"] in self.pending:
                    future = self.pending[value["id"]]
                    if not future.done():
                        future.set_result(value)
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(NativeConnectionFailure("Native stream disconnected"))

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        profile = self.profile or require_version(self.version)
        if method not in profile.read_methods:
            raise ValueError("Native consumer permits only read/subscription requests")
        if method == "thread/resume" and set(params) != {"threadId", "excludeTurns"}:
            raise ValueError("Native subscription cannot change configuration")
        if self.reader is None or self.reader.done() or self.socket is None:
            raise NativeConnectionFailure("Native connection unavailable")
        self.counter += 1
        key = self.counter
        future = asyncio.get_running_loop().create_future()
        self.pending[key] = future
        try:
            await self.socket.send(json.dumps({"id": key, "method": method, "params": params}))
            try:
                async with asyncio.timeout(10):
                    response = await future
            except TimeoutError:
                raise NativeConnectionFailure("Native read timed out") from None
            if "error" in response or not isinstance(response.get("result"), dict):
                # Never propagate/log native error text, which may contain private content.
                raise NativeReadFailure("Native read request rejected")
            return response["result"]
        finally:
            self.pending.pop(key, None)

    async def __aexit__(self, *_: object) -> None:
        if self.socket:
            await self.socket.close()
        if self.reader:
            await asyncio.gather(self.reader, return_exceptions=True)
