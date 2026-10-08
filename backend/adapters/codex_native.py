"""Normalize confirmed Codex facts into OfficeRuntime; no transport or raw-content storage."""

import asyncio
import hashlib
from collections import OrderedDict
from dataclasses import replace
from datetime import datetime

from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.native.codex.activity import Activity, ReplayCache
from backend.native.codex.bindings import (
    BindingConflict,
    BindingRegistry,
    NativeThreadBinding,
    same_generation,
)
from backend.native.codex.protocol import Fact, NativeUnavailable, ThreadMetadata
from backend.runtime.office import OfficeRuntime


class CodexNativeAdapter:
    def __init__(
        self, runtime: OfficeRuntime, bindings: BindingRegistry, terminal_seconds: float
    ) -> None:
        self.runtime = runtime
        self.bindings = bindings
        self.terminal_seconds = terminal_seconds
        self.activities: dict[str, Activity] = {}
        self.replay = ReplayCache()
        self.finished = ReplayCache()
        self.retired_turns = ReplayCache(capacity=1024)
        self.completed_children: set[str] = set()  # Bounded by sticky binding capacity.
        self.cleanup_tasks: dict[str, asyncio.Task[None]] = {}
        self.last_display: dict[str, tuple[object, ...]] = {}
        self.request_keys: OrderedDict[tuple[str, str], tuple[str | None, str | None]] = (
            OrderedDict()
        )

    async def emit(self, agent_id: str, kind: AgentEventType, **payload: object) -> None:
        await self.runtime.apply(
            AgentEvent(
                type=kind,
                agent_id=agent_id,
                source=EventSource.NATIVE,
                payload=payload,
            )
        )

    def activity(self, thread: str) -> Activity:
        return self.activities.setdefault(thread, Activity())

    def live(self, thread: str) -> NativeThreadBinding | None:
        binding = self.bindings.by_thread.get(thread)
        if binding is None or thread in self.completed_children:
            return None
        try:
            agent = self.runtime.registry.get(binding.office_agent_id)
        except KeyError:
            return None
        return binding if same_generation(agent.started_at, binding.generation) else None

    async def display(
        self, thread: str, *, force: bool = False, exit_code: int | None = None
    ) -> None:
        if not (binding := self.live(thread)):
            return
        activity = self.activity(thread)
        if (
            sum(map(len, (activity.commands, activity.files, activity.requests, activity.waits)))
            > 256
        ):
            raise NativeUnavailable("Native active-item limit reached")
        derived = activity.derive()
        if derived == self.last_display.get(thread) and not force and exit_code is None:
            return
        state, tool, reason, child, released = derived
        payload: dict[str, object] = {
            "to": state,
            "current_tool": tool,
            "waiting_reason": reason,
            "waiting_on_agent_id": child,
            "release_evidence": released,
        }
        if exit_code is not None:
            payload["native_exit_code"] = exit_code
        await self.emit(binding.office_agent_id, AgentEventType.STATE_CHANGED, **payload)
        self.last_display[thread] = derived

    async def create_child(
        self, parent: str, metadata: ThreadMetadata, *, reopen: bool = False
    ) -> None:
        if (
            not (owner := self.live(parent))
            or metadata.parent != parent
            or metadata.thread == parent
        ):
            raise BindingConflict("Native child parent does not match the observed delegation")
        thread = metadata.thread
        if thread in self.completed_children and not reopen:
            return
        if thread in self.bindings.by_thread:
            previous = self.bindings.by_thread[thread]
            if (
                previous.root_thread_id != owner.root_thread_id
                or previous.parent_thread_id != parent
            ):
                raise BindingConflict("Native child is already owned by another binding")
            if self.live(thread) or not reopen:
                return
        parent_agent = self.runtime.registry.get(owner.office_agent_id)
        identifier = "codex-child-" + hashlib.sha256(thread.encode()).hexdigest()[:24]
        if any(a.id == identifier for a in self.runtime.registry.all()):
            raise BindingConflict("Generated native child identity already exists")
        agent = Agent(
            id=identifier,
            name=metadata.native_nickname or "Codex subagent",
            provider="codex",
            repository=parent_agent.repository,
            worktree=str(metadata.cwd),
            parent_agent_id=owner.office_agent_id,
            definition_id=owner.child_definition_id,
            role=metadata.role,
            status=AgentState.STARTING,
            metadata={"native_nickname": metadata.native_nickname, "name_is_generated": True},
        )
        if previous := self.bindings.by_thread.get(thread):
            agent.started_at = datetime.fromisoformat(previous.generation)
        binding = NativeThreadBinding(
            identifier,
            thread,
            owner.root_thread_id,
            agent.started_at.isoformat(),
            owner.child_definition_id,
            parent,
        )
        self.bindings.check(binding)
        await self.emit(
            identifier, AgentEventType.AGENT_STARTED, agent=agent.model_dump(mode="json")
        )
        self.bindings.add(binding)
        self.completed_children.discard(thread)

    async def handle(self, fact: Fact) -> None:
        if not self.live(fact.thread):
            return
        activity = self.activity(fact.thread)
        if fact.kind == "status":
            # Status notifications lack event IDs: dedup derived values rather than a global key.
            activity.idle = fact.phase == "idle"
            if fact.phase != "idle" or not activity.waiting_flag:
                activity.waiting_flag = fact.waiting
            await self.display(fact.thread)
            return
        if fact.kind == "resolved":
            turn, item = self.request_keys.get((fact.thread, fact.request or ""), (None, None))
            fact = replace(fact, turn=turn, item=item)
        if not self.replay.add(fact.key()) and fact.kind != "request":
            return
        if fact.turn and (fact.thread, fact.turn) in self.retired_turns.entries:
            return
        if fact.kind == "request":
            request_key = (fact.thread, "request", fact.turn, fact.item, fact.request)
            if fact.request and request_key not in self.finished.entries:
                activity.requests.add(fact.request)
                key = (fact.thread, fact.request)
                self.request_keys[key] = (fact.turn, fact.item)
                self.request_keys.move_to_end(key)
                if len(self.request_keys) > 8192:
                    self.request_keys.popitem(last=False)
                activity.waiting_flag = False  # The correlated request now owns this wait.
        elif fact.kind == "resolved":
            turn, item = self.request_keys.get((fact.thread, fact.request or ""), (None, None))
            self.finished.add((fact.thread, "request", turn, item, fact.request))
            activity.requests.discard(fact.request or "")
            if not activity.requests:
                activity.waiting_flag = False
        elif fact.kind == "turn":
            previous_turn = activity.latest_turn
            activity.latest_turn = fact.turn
            if fact.phase == "inProgress":
                if previous_turn and previous_turn != fact.turn:
                    self.retired_turns.add((fact.thread, previous_turn))
                    activity.clear_active()
                await self.cancel_cleanup(fact.thread)
                activity.terminal = None
                activity.terminal_turn = None
                activity.idle = False
            else:
                self.retired_turns.add((fact.thread, fact.turn))
                activity.clear_active()
                activity.idle = True
                if fact.phase == "failed":
                    activity.terminal = AgentState.ERROR
                    activity.terminal_turn = fact.turn
                binding = self.bindings.by_thread[fact.thread]
                if (
                    binding.thread_id != binding.root_thread_id
                    and fact.phase == "completed"
                    and activity.terminal is not AgentState.ERROR
                ):
                    activity.terminal = AgentState.DONE
                    activity.terminal_turn = fact.turn
        elif fact.kind in {"command", "file", "wait"}:
            key = (fact.turn, fact.item)
            if fact.phase == "start" and (fact.thread, *key) in self.finished.entries:
                return
            if fact.phase == "finish":
                self.finished.add((fact.thread, *key))
            if fact.kind == "command":
                if fact.phase == "start":
                    activity.commands[key] = fact
                    activity.idle = False
                else:
                    activity.commands.pop(key, None)
            elif fact.kind == "file":
                if fact.phase == "start":
                    activity.files.add(key)
                    activity.idle = False
                else:
                    activity.files.discard(key)
                    binding = self.bindings.by_thread[fact.thread]
                    for path in fact.paths if fact.successful is not False else ():
                        await self.emit(
                            binding.office_agent_id, AgentEventType.FILE_CHANGED, file=path
                        )
            else:
                if fact.phase == "finish":
                    activity.waits.pop(key, None)
                elif len(fact.recipients) == 1:
                    child = self.bindings.by_thread.get(fact.recipients[0])
                    if (
                        child
                        and self.live(child.thread_id)
                        and self.runtime.registry.get(child.office_agent_id).parent_agent_id
                        == (self.bindings.by_thread[fact.thread].office_agent_id)
                    ):
                        activity.waits[key] = child.office_agent_id
        # No blanket parent wait just because a child is active.
        await self.display(fact.thread, exit_code=fact.exit_code)
        if activity.terminal and self.bindings.by_thread[fact.thread].root_thread_id != fact.thread:
            self.schedule_cleanup(fact.thread)

    async def child_completed(self, thread: str, successful: bool) -> None:
        if not self.live(thread):
            return
        activity = self.activity(thread)
        activity.clear_active()
        if activity.terminal is not AgentState.ERROR:
            activity.terminal = AgentState.DONE if successful else AgentState.ERROR
            activity.terminal_turn = activity.latest_turn
        await self.display(thread)
        self.schedule_cleanup(thread)

    def schedule_cleanup(self, thread: str) -> None:
        if thread not in self.cleanup_tasks:
            self.cleanup_tasks[thread] = asyncio.create_task(self._cleanup(thread))

    async def cancel_cleanup(self, thread: str) -> None:
        if task := self.cleanup_tasks.pop(thread, None):
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    async def _cleanup(self, thread: str) -> None:
        try:
            await asyncio.sleep(self.terminal_seconds)
            if binding := self.live(thread):
                await self.emit(binding.office_agent_id, AgentEventType.AGENT_STOPPED)
            self.completed_children.add(thread)
            self.activities.pop(thread, None)
            self.last_display.pop(thread, None)
        finally:
            self.cleanup_tasks.pop(thread, None)

    async def release(self, root: str, *, thread_only: bool = False) -> None:
        for thread, binding in self.bindings.by_thread.items():
            if (thread != root if thread_only else binding.root_thread_id != root) or not self.live(
                thread
            ):
                continue
            activity = self.activity(thread)
            activity.clear_active()
            self.last_display.pop(thread, None)
            agent = self.runtime.registry.get(binding.office_agent_id)
            evidence = self.runtime.status_evidence(agent.id)
            if (
                evidence.source is EventSource.NATIVE
                and not evidence.released
                and agent.status not in {AgentState.DONE, AgentState.ERROR, AgentState.OFFLINE}
            ):
                # Do not reset accepted wrapper terminal states; no disconnect-as-death event.
                state = (
                    agent.status
                    if agent.status in {AgentState.DONE, AgentState.ERROR}
                    else (AgentState.THINKING)
                )
                await self.emit(
                    agent.id,
                    AgentEventType.STATE_CHANGED,
                    to=state,
                    current_tool=None,
                    waiting_reason=None,
                    waiting_on_agent_id=None,
                    release_evidence=state not in {AgentState.DONE, AgentState.ERROR},
                )

    async def stop(self) -> None:
        tasks = list(self.cleanup_tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
