"""Opt-in consumer of explicitly selected, already-loaded daemon threads."""

import asyncio
from pathlib import Path
from typing import Any

from backend.adapters.codex_native import CodexNativeAdapter
from backend.config import CodexNativeSettings
from backend.models import AgentState
from backend.native.codex.bindings import BindingConflict, BindingRegistry, NativeThreadBinding
from backend.native.codex.protocol import (
    Fact,
    NativeUnavailable,
    ThreadMetadata,
    parse_event,
    require_version,
)
from backend.native.codex.transport import ReadOnlyClient, discover
from backend.runtime.office import OfficeRuntime


class CodexNativeConsumer:
    def __init__(self, runtime: OfficeRuntime, settings: CodexNativeSettings) -> None:
        self.runtime = runtime
        self.settings = settings
        self.bindings = BindingRegistry()
        self.adapter = CodexNativeAdapter(runtime, self.bindings, settings.terminal_seconds)
        self.tasks: dict[str, asyncio.Task[None]] = {}
        self.states: dict[str, str] = {}
        self.version: str | None = None
        self.failures: dict[str, str] = {}
        self.workspaces: dict[str, Path] = {}
        self.validation_roots: dict[str, tuple[Path, ...]] = {}
        self.lock = asyncio.Lock()
        self.stopping = False

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.settings.enabled,
            "version": self.version,
            "bindings": [
                {
                    "office_agent_id": b.office_agent_id,
                    "thread_id": b.thread_id,
                    "root_thread_id": b.root_thread_id,
                    "status": self.states.get(b.root_thread_id),
                    "failure_type": self.failures.get(b.root_thread_id),
                }
                for b in self.bindings.by_thread.values()
            ],
        }

    async def connection_info(self) -> tuple[str, Path]:
        version, socket = await discover(self.settings.codex_binary)
        self.version = version
        require_version(version)
        if self.settings.socket_path and self.settings.socket_path != socket:
            raise NativeUnavailable("Configured socket does not match the running daemon")
        return version, socket

    async def bind(
        self,
        office_agent_id: str,
        thread_id: str,
        child_definition_id: str | None = None,
    ) -> NativeThreadBinding:
        if not self.settings.enabled:
            raise NativeUnavailable("Codex native integration is disabled")
        async with self.lock:
            agent = self.runtime.registry.get(office_agent_id)
            if agent.provider != "codex":
                raise BindingConflict("Only a Codex Office Agent can bind a Codex thread")
            binding = NativeThreadBinding(
                agent.id,
                thread_id,
                thread_id,
                agent.started_at.isoformat(),
                child_definition_id,
            )
            self.bindings.check(binding)
            version, socket = await self.connection_info()

            async def ignore(_: dict[str, Any]) -> None:
                pass

            async with ReadOnlyClient(socket, version, ignore) as client:
                metadata = await self.read_metadata(client, thread_id)
                await self.validate_workspace(metadata, office_agent_id)
            if self.runtime.registry.get(agent.id).started_at.isoformat() != binding.generation:
                raise BindingConflict("Office Agent changed during the binding handshake")
            self.bindings.add(binding)
            self.workspaces[thread_id] = metadata.cwd
            self.validation_roots[thread_id] = tuple(
                Path(path) for path in (agent.repository, agent.worktree) if path
            )
            if thread_id not in self.tasks or self.tasks[thread_id].done():
                self.tasks[thread_id] = asyncio.create_task(self._run(binding))
            return binding

    async def read_metadata(self, client: ReadOnlyClient, thread: str) -> ThreadMetadata:
        response = await client.request("thread/read", {"threadId": thread, "includeTurns": False})
        value = response.get("thread")
        if not isinstance(value, dict):
            raise NativeUnavailable("Malformed thread metadata")
        metadata = ThreadMetadata.parse(value)
        if metadata.thread != thread:
            raise NativeUnavailable("Native thread identity mismatch")
        return metadata

    async def validate_workspace(self, metadata: ThreadMetadata, agent_id: str) -> None:
        binding = self.bindings.by_agent.get(agent_id)
        if binding and binding.root_thread_id in self.validation_roots:
            paths = self.validation_roots[binding.root_thread_id]
        else:
            agent = self.runtime.registry.get(agent_id)
            paths = tuple(Path(path) for path in (agent.repository, agent.worktree) if path)

        def valid() -> bool:
            roots = [path.resolve() for path in paths]
            return metadata.cwd.resolve() in roots

        if not await asyncio.to_thread(valid):
            raise BindingConflict("Native thread workspace does not match the bound Office Agent")

    def has_live_threads(self, root: str) -> bool:
        return any(
            b.root_thread_id == root and self.adapter.live(b.thread_id)
            for b in self.bindings.by_thread.values()
        )

    async def _run(self, binding: NativeThreadBinding) -> None:
        root = binding.thread_id
        while not self.stopping and self.has_live_threads(root):
            try:
                self.states[root] = "connecting"
                version, socket = await self.connection_info()
                queue: asyncio.Queue[Fact] = asyncio.Queue(maxsize=512)
                workspace = self.workspaces[root]

                async def receive(
                    value: dict[str, Any],
                    scope_path: Path = workspace,
                    events: asyncio.Queue[Fact] = queue,
                ) -> None:
                    params = value.get("params")
                    if not isinstance(params, dict):
                        return
                    thread = params.get("threadId")
                    if not isinstance(thread, str):
                        return
                    selected = self.bindings.by_thread.get(thread)
                    if (
                        selected is None
                        or selected.root_thread_id != root
                        or not self.adapter.live(thread)
                    ):
                        return
                    fact = await asyncio.to_thread(
                        parse_event, value, self.workspaces.get(thread, scope_path)
                    )
                    if fact is not None:
                        try:
                            events.put_nowait(fact)
                        except asyncio.QueueFull:
                            raise NativeUnavailable("Native event backlog limit reached") from None

                async with ReadOnlyClient(socket, version, receive) as client:
                    if self.adapter.live(root):
                        metadata = await self.read_metadata(client, root)
                        await self.validate_workspace(metadata, binding.office_agent_id)
                        # Check loaded status before resume; never load historical threads.
                        await client.request(
                            "thread/resume", {"threadId": root, "excludeTurns": True}
                        )
                        await self.reconcile(client, root, metadata, queue)
                    else:
                        await self.restore_children(client, root)
                    self.states[root] = "connected"
                    self.failures.pop(root, None)
                    while self.has_live_threads(root) and not self.stopping:
                        if client.reader is None or client.reader.done():
                            raise NativeUnavailable("Native source disconnected")
                        try:
                            fact = await asyncio.wait_for(queue.get(), timeout=0.25)
                        except TimeoutError:
                            continue
                        await self.consume(client, fact)
            except asyncio.CancelledError:
                raise
            except Exception as error:
                # No raw exception strings, native error bodies, config or prompts in logs/status.
                self.states[root] = "unavailable"
                self.failures[root] = type(error).__name__
            finally:
                await self.adapter.release(root)
            await asyncio.sleep(self.settings.reconnect_seconds)
        self.states[root] = "inactive"

    async def consume(self, client: ReadOnlyClient, fact: Fact) -> None:
        if fact.kind == "child" and fact.child:
            if fact.key() in self.adapter.replay.entries:
                return
            metadata = await self.read_metadata(client, fact.child)
            parent_binding = self.bindings.by_thread[fact.thread]
            await self.validate_workspace(metadata, parent_binding.office_agent_id)
            reopen = False
            if fact.child in self.adapter.completed_children:
                if fact.phase != "started" or metadata.status != "active":
                    return
                turns = await client.request(
                    "thread/turns/list",
                    {
                        "threadId": fact.child,
                        "limit": 1,
                        "itemsView": "notLoaded",
                    },
                )
                data = turns.get("data", [])
                if not data or data[0].get("status") != "inProgress":
                    return
                if (fact.child, data[0].get("id")) in self.adapter.retired_turns.entries:
                    return
                reopen = True
            await self.adapter.create_child(fact.thread, metadata, reopen=reopen)
            self.workspaces[fact.child] = metadata.cwd
            # Native child activity corroborates the metadata relationship before subscription.
            await client.request("thread/resume", {"threadId": fact.child, "excludeTurns": True})
            await self.hydrate_thread(client, fact.child)
            if fact.phase == "completed":
                # Activity completion alone isn't proof of success. Inspect exact child's turn.
                turns = await client.request(
                    "thread/turns/list",
                    {
                        "threadId": fact.child,
                        "limit": 1,
                        "itemsView": "notLoaded",
                    },
                )
                data = turns.get("data", [])
                if data and data[0].get("status") in {"completed", "failed"}:
                    await self.adapter.child_completed(
                        fact.child,
                        successful=data[0]["status"] == "completed",
                    )
            self.adapter.replay.add(fact.key())
            return
        await self.adapter.handle(fact)

    async def hydrate_thread(self, client: ReadOnlyClient, thread: str) -> None:
        """Rebuild current activity from bounded structural snapshots, not raw-history replay."""
        metadata = await self.read_metadata(client, thread)
        result = await client.request(
            "thread/turns/list",
            {
                "threadId": thread,
                "limit": 1,
                "itemsView": "notLoaded",
            },
        )
        turns = result.get("data")
        if not isinstance(turns, list):
            raise NativeUnavailable("Malformed native turn snapshot")
        activity = self.adapter.activity(thread)
        activity.clear_active()
        if turns:
            turn = turns[0]
            if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
                raise NativeUnavailable("Malformed native turn identity")
            items = await self.items(client, thread, turn["id"])
            if turn.get("status") == "inProgress":
                await self.adapter.cancel_cleanup(thread)
                activity.terminal = None
                activity.terminal_turn = None
                activity.latest_turn = turn["id"]
                activity.idle = False
                for fact in items:
                    if fact.phase != "start":
                        if fact.kind in {"command", "file", "wait"}:
                            self.adapter.finished.add((thread, fact.turn, fact.item))
                        continue
                    if fact.kind in {"command", "file", "wait"}:
                        # Snapshot hydration is not another event; keep replay keys intact.
                        key = (fact.turn, fact.item)
                        if fact.kind == "command":
                            activity.commands[key] = fact
                        elif fact.kind == "file":
                            activity.files.add(key)
                        elif len(fact.recipients) == 1:
                            child = self.bindings.by_thread.get(fact.recipients[0])
                            if (
                                child
                                and self.adapter.live(child.thread_id)
                                and child.parent_thread_id == thread
                            ):
                                activity.waits[key] = child.office_agent_id
            elif turn.get("status") in {"completed", "failed", "interrupted"}:
                if activity.terminal_turn != turn["id"]:
                    activity.terminal = None
                if turn["status"] == "failed":
                    activity.terminal = AgentState.ERROR
                elif self.bindings.by_thread[thread].root_thread_id != thread:
                    if turn["status"] == "completed" and activity.terminal is not AgentState.ERROR:
                        activity.terminal = AgentState.DONE
                activity.terminal_turn = turn["id"] if activity.terminal else None
                activity.latest_turn = turn["id"]
                self.adapter.retired_turns.add((thread, turn["id"]))
                if activity.terminal and self.bindings.by_thread[thread].root_thread_id != thread:
                    self.adapter.schedule_cleanup(thread)
        activity.idle = metadata.status == "idle"
        activity.waiting_flag = metadata.waiting
        await self.adapter.display(thread, force=True)

    async def restore_children(self, client: ReadOnlyClient, root: str) -> None:
        for thread, binding in list(self.bindings.by_thread.items()):
            if thread == root or binding.root_thread_id != root or not self.adapter.live(thread):
                continue
            metadata = await self.read_metadata(client, thread)
            await self.validate_workspace(metadata, binding.office_agent_id)
            self.workspaces[thread] = metadata.cwd
            await client.request("thread/resume", {"threadId": thread, "excludeTurns": True})
            await self.hydrate_thread(client, thread)

    async def items(self, client: ReadOnlyClient, thread: str, turn: str) -> list[Fact]:
        items: list[Fact] = []
        cursor = None
        count = 0
        workspace = self.workspaces.get(thread)
        if workspace is None:
            binding = self.bindings.by_thread[thread]
            agent = self.runtime.registry.get(binding.office_agent_id)
            workspace = Path(agent.worktree or agent.repository)
        for _ in range(8):
            page = await client.request(
                "thread/items/list",
                {
                    "threadId": thread,
                    "turnId": turn,
                    "limit": 100,
                    "cursor": cursor,
                },
            )
            data = page.get("data")
            if not isinstance(data, list):
                raise NativeUnavailable("Malformed native item snapshot")
            for entry in data:
                item = entry.get("item") if isinstance(entry, dict) else None
                if not isinstance(item, dict):
                    raise NativeUnavailable("Malformed native item entry")
                fact = await asyncio.to_thread(
                    parse_event,
                    {
                        "method": "item/started"
                        if item.get("status") == "inProgress"
                        or item.get("type") == "subAgentActivity"
                        else "item/completed",
                        "params": {"threadId": thread, "turnId": turn, "item": item},
                    },
                    workspace,
                )
                if fact:
                    items.append(fact)
                count += 1
            if count > 800:
                raise NativeUnavailable("Native reconciliation item limit reached")
            cursor = page.get("nextCursor")
            if cursor is None:
                return items
        raise NativeUnavailable("Native reconciliation item limit reached")

    async def reconcile(
        self,
        client: ReadOnlyClient,
        root: str,
        metadata: ThreadMetadata,
        queue: asyncio.Queue[Fact],
    ) -> None:
        # Search only the explicitly bound thread, and stop at the previously observed turn.
        checkpoint = self.adapter.activity(root).latest_turn
        turns: list[dict[str, Any]] = []
        cursor = None
        for _ in range(4):
            result = await client.request(
                "thread/turns/list",
                {
                    "threadId": root,
                    "limit": 8 if checkpoint else 1,
                    "cursor": cursor,
                    "itemsView": "notLoaded",
                },
            )
            data = result.get("data")
            if not isinstance(data, list):
                raise NativeUnavailable("Malformed native turn page")
            reached = False
            for turn in data:
                if not isinstance(turn, dict) or not isinstance(turn.get("id"), str):
                    raise NativeUnavailable("Malformed native turn identity")
                turns.append({"id": turn["id"], "status": turn.get("status")})
                if checkpoint is None or turn["id"] == checkpoint:
                    reached = True
                    break
            cursor = result.get("nextCursor")
            if reached or cursor is None:
                break
        else:
            raise NativeUnavailable("Native reconciliation turn limit reached")
        children: dict[str, Fact] = {}
        for turn in reversed(turns):
            for fact in await self.items(client, root, turn["id"]):
                if fact.kind == "child" and fact.child:
                    children[fact.child] = fact
        for fact in children.values():
            # Do not manufacture a past completed child from an initial subscription snapshot.
            if fact.phase == "completed" and fact.child not in self.bindings.by_thread:
                continue
            await self.consume(client, fact)
        await self.restore_children(client, root)
        await self.hydrate_thread(client, root)
        # Requests replayed by subscription are processed after reconstruction. Finished request
        # tombstones prevent an already-resolved request resurrecting a wait.
        while not queue.empty():
            await self.consume(client, queue.get_nowait())

    async def reconnect(self, office_agent_id: str) -> None:
        async with self.lock:
            binding = self.bindings.by_agent[office_agent_id]
            root = binding.root_thread_id
            if task := self.tasks.get(root):
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            owner = self.bindings.by_thread[root]
            if self.has_live_threads(root):
                self.tasks[root] = asyncio.create_task(self._run(owner))

    async def stop(self) -> None:
        self.stopping = True
        tasks = list(self.tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.adapter.stop()
