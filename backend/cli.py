import argparse
import os
import re
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from backend.config import Settings
from backend.models import Agent, AgentEvent, AgentEventType, AgentState
from backend.observer.git import GitObserver
from backend.runtime.emitters import FallbackEventEmitter, HttpEventEmitter, JsonlEventEmitter
from backend.runtime.storage import EventStorage


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
) -> int:
    repository = repository.resolve()
    git = GitObserver(repository).snapshot()
    identifier = agent_id or _identifier(name)
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": identifier,
        "AGENT_OFFICE_NAME": name,
        "AGENT_OFFICE_PROVIDER": provider,
        "AGENT_OFFICE_REPOSITORY": str(repository),
        "AGENT_OFFICE_TASK": task or "",
        "AGENT_OFFICE_ROLE": role or "",
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
        metadata={"command": list(command)},
    )
    emitter(
        AgentEvent(
            type=AgentEventType.AGENT_STARTED,
            agent_id=identifier,
            payload={"agent": agent.model_dump(mode="json")},
        )
    )
    emitter(
        AgentEvent(
            type=AgentEventType.TOOL_STARTED,
            agent_id=identifier,
            payload={"tool": provider, "command": list(command)},
        )
    )
    exit_code = process.wait()
    if exit_code:
        emitter(
            AgentEvent(
                type=AgentEventType.ERROR,
                agent_id=identifier,
                payload={"message": f"Process exited with status {exit_code}"},
            )
        )
    emitter(
        AgentEvent(
            type=AgentEventType.TOOL_FINISHED,
            agent_id=identifier,
            payload={"tool": provider, "exit_code": exit_code, "next_state": "done"},
        )
    )
    emitter(AgentEvent(type=AgentEventType.AGENT_STOPPED, agent_id=identifier))
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="office-run", description="Run an agent inside Agent Office"
    )
    parser.add_argument("provider", help="Executable/provider name, for example codex or claude")
    parser.add_argument("--id", dest="agent_id")
    parser.add_argument("--name")
    parser.add_argument("--role")
    parser.add_argument("--task")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--server", default="http://127.0.0.1:8000/api/events")
    parser.add_argument("--events", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args, agent_args = build_parser().parse_known_args(argv)
    settings = Settings.load()
    event_path = args.events or settings.runtime_path
    emitter = FallbackEventEmitter(
        HttpEventEmitter(args.server),
        JsonlEventEmitter(EventStorage(event_path)),
    )
    try:
        exit_code = run_wrapped(
            [args.provider, *agent_args],
            name=args.name or args.provider.title(),
            provider=args.provider,
            repository=args.repo,
            role=args.role,
            task=args.task,
            emitter=emitter,
            agent_id=args.agent_id,
        )
    except FileNotFoundError as error:
        build_parser().error(f"executable not found: {error.filename}")
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
