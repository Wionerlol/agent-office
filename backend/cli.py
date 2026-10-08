import argparse
import json
import os
import re
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path
from uuid import uuid4

from backend.config import Settings
from backend.models import Agent, AgentEvent, AgentEventType, AgentState, EventSource
from backend.native_cli import BindingHandshake, explicit_thread
from backend.observer.git import GitObserver
from backend.runtime.emitters import HttpEventEmitter
from backend.state.identity import responsibilities_from_environment


def _identifier(name: str) -> str:
    identifier = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return identifier or "agent"


def run_wrapped(
    command: Sequence[str],
    *,
    name: str,
    provider: str,
    repository: Path,
    role: str | None,
    task: str | None,
    emitter: Callable[[AgentEvent], None],
    agent_id: str | None = None,
    parent_agent_id: str | None = None,
    definition_id: str | None = None,
    responsibilities: list[str] | None = None,
    native_handshake: BindingHandshake | None = None,
) -> int:
    repository = repository.resolve()
    git = GitObserver(repository).snapshot()
    definition_id = definition_id or os.environ.get("AGENT_OFFICE_DEFINITION_ID") or None
    parent_agent_id = parent_agent_id or os.environ.get("AGENT_OFFICE_PARENT_ID") or None
    role = role or os.environ.get("AGENT_OFFICE_ROLE") or None
    responsibilities = (
        responsibilities
        if responsibilities is not None
        else responsibilities_from_environment(os.environ)
    )
    identifier = agent_id or (
        f"{_identifier(definition_id)}-{uuid4().hex}" if definition_id else _identifier(name)
    )
    if parent_agent_id == identifier:
        raise ValueError("An agent cannot be its own parent")
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": identifier,
        "AGENT_OFFICE_NAME": name,
        "AGENT_OFFICE_PROVIDER": provider,
        "AGENT_OFFICE_REPOSITORY": str(repository),
        "AGENT_OFFICE_TASK": task or "",
        "AGENT_OFFICE_ROLE": role or "",
        "AGENT_OFFICE_PARENT_ID": parent_agent_id or "",
        "AGENT_OFFICE_DEFINITION_ID": definition_id or "",
        "AGENT_OFFICE_RESPONSIBILITIES": json.dumps(responsibilities),
        "AGENT_OFFICE_WORKTREE": git.worktree,
        "AGENT_OFFICE_BRANCH": git.branch or "",
    }
    process = subprocess.Popen(list(command), cwd=repository, env=environment)
    agent = Agent(
        id=identifier,
        name=name,
        provider=provider,
        pid=process.pid,
        repository=str(repository),
        worktree=git.worktree,
        branch=git.branch,
        status=AgentState.STARTING,
        task=task,
        role=role,
        parent_agent_id=parent_agent_id,
        definition_id=definition_id,
        responsibilities=responsibilities,
        metadata={"command": list(command)},
    )
    emitter(
        AgentEvent(
            source=EventSource.WRAPPER,
            type=AgentEventType.AGENT_STARTED,
            agent_id=identifier,
            payload={"agent": agent.model_dump(mode="json")},
        )
    )
    emitter(
        AgentEvent(
            source=EventSource.WRAPPER,
            type=AgentEventType.STATE_CHANGED,
            agent_id=identifier,
            payload={"from": "starting", "to": "thinking"},
        )
    )
    if native_handshake:
        native_handshake.start(agent)
    try:
        exit_code = process.wait()
    finally:
        if native_handshake:
            native_handshake.close()
    if exit_code:
        emitter(
            AgentEvent(
                source=EventSource.WRAPPER,
                type=AgentEventType.ERROR,
                agent_id=identifier,
                payload={"message": f"Process exited with status {exit_code}"},
            )
        )
    if not exit_code:
        emitter(
            AgentEvent(
                source=EventSource.WRAPPER,
                type=AgentEventType.STATE_CHANGED,
                agent_id=identifier,
                payload={"to": "done"},
            )
        )
    emitter(
        AgentEvent(
            type=AgentEventType.AGENT_STOPPED,
            agent_id=identifier,
            source=EventSource.WRAPPER,
            payload={"pid": process.pid},
        )
    )
    return exit_code


def _server_endpoint(settings: Settings) -> str:
    host = settings.server.host
    if host in {"0.0.0.0", "::", "[::]"}:
        host = "127.0.0.1"
    return f"http://{host}:{settings.server.port}/api/events"


def load_cli_settings() -> Settings:
    return Settings.load_default()


def build_parser(settings: Settings | None = None) -> argparse.ArgumentParser:
    settings = settings or Settings()
    parser = argparse.ArgumentParser(
        prog="office-run", description="Run an agent inside Agent Office", allow_abbrev=False
    )
    parser.add_argument("provider", help="Executable/provider name, for example codex or claude")
    parser.add_argument("--id", dest="agent_id")
    parser.add_argument("--name")
    parser.add_argument("--role")
    parser.add_argument("--parent", dest="parent_agent_id")
    parser.add_argument("--definition", dest="definition_id")
    parser.add_argument("--responsibility", dest="responsibilities", action="append")
    parser.add_argument("--task")
    parser.add_argument("--native-thread")
    parser.add_argument("--native-child-definition")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--server", default=_server_endpoint(settings))
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    settings = load_cli_settings()
    parser = build_parser(settings)
    args, agent_args = parser.parse_known_args(argv)
    emitter = HttpEventEmitter(args.server)
    if agent_args and agent_args[0] == "--":
        agent_args = agent_args[1:]  # Wrapper delimiter, including DevRouter's launch format.
    try:
        thread = (
            explicit_thread(
                [args.provider, *agent_args],
                args.native_thread or os.environ.get("AGENT_OFFICE_NATIVE_THREAD_ID"),
            )
            if args.provider == "codex"
            else None
        )
        handshake = (
            BindingHandshake(
                args.server,
                thread,
                args.native_child_definition
                or os.environ.get("AGENT_OFFICE_NATIVE_CHILD_DEFINITION"),
            )
            if thread
            else None
        )
        exit_code = run_wrapped(
            [args.provider, *agent_args],
            name=args.name or os.environ.get("AGENT_OFFICE_NAME") or args.provider.title(),
            provider=args.provider,
            repository=args.repo,
            role=args.role,
            task=args.task,
            emitter=emitter,
            agent_id=args.agent_id,
            parent_agent_id=args.parent_agent_id,
            definition_id=args.definition_id,
            responsibilities=args.responsibilities,
            native_handshake=handshake,
        )
    except FileNotFoundError as error:
        parser.error(f"executable not found: {error.filename}")
    except ValueError as error:
        parser.error(str(error))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
