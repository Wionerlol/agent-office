"""Local native control-plane commands and explicit office-run binding handshake."""

import argparse
import asyncio
import ipaddress
import json
import logging
import threading
import time
from collections.abc import Sequence
from urllib.parse import quote, urlsplit
from uuid import UUID

import httpx

from backend.config import Settings
from backend.models import Agent
from backend.native.codex.diagnostics import validate_runtime

logger = logging.getLogger(__name__)


def local_server(url: str) -> str:
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    try:
        local = ipaddress.ip_address(host).is_loopback
    except ValueError:
        local = host == "localhost"
    if parsed.scheme != "http" or not local or parsed.username or parsed.password:
        raise ValueError("Native commands require a loopback HTTP server")
    return f"http://{parsed.netloc}"


def explicit_thread(command: Sequence[str], supplied: str | None) -> str | None:
    """Only a literal resume UUID is launch evidence; never names, --last or a picker."""
    resumed = None
    if len(command) >= 3 and command[1] == "resume":
        try:
            resumed = str(UUID(command[2]))
        except ValueError:
            pass
    selected = str(UUID(supplied)) if supplied else resumed
    if resumed and selected != resumed:
        raise ValueError("Explicit native thread conflicts with Codex resume UUID")
    return selected


class BindingHandshake:
    def __init__(self, server: str, thread: str, child_definition: str | None = None) -> None:
        self.server = local_server(server)
        self.thread = thread
        self.child_definition = child_definition
        self.cancelled = threading.Event()
        self.worker: threading.Thread | None = None

    def start(self, agent: Agent) -> None:
        self.worker = threading.Thread(target=self._bind, args=(agent,), daemon=True)
        self.worker.start()

    def _bind(self, agent: Agent) -> None:
        deadline = time.monotonic() + 30
        with httpx.Client(base_url=self.server, timeout=2) as client:
            while not self.cancelled.is_set() and time.monotonic() < deadline:
                try:
                    if not client.get("/api/native/codex").json().get("enabled"):
                        return
                    response = client.post(
                        "/api/native/codex/bind",
                        json={
                            "office_agent_id": agent.id,
                            "thread_id": self.thread,
                            "expected_generation": agent.started_at.isoformat(),
                            "child_definition_id": self.child_definition,
                        },
                    )
                    if response.status_code == 200:
                        return
                    if response.status_code in {409, 422}:
                        logger.warning("Native binding conflict; agent remains on fallback")
                        return
                except (httpx.HTTPError, ValueError, OSError):
                    pass
                self.cancelled.wait(0.5)
        if not self.cancelled.is_set():
            logger.warning("Native binding unavailable; use agent-office native bind to retry")

    def close(self) -> None:
        self.cancelled.set()
        if self.worker:
            self.worker.join(timeout=3)


def main(argv: Sequence[str]) -> None:
    settings = Settings.load_default()
    host = settings.server.host
    if host in {"0.0.0.0", "::", "[::]"}:
        host = "127.0.0.1"
    parser = argparse.ArgumentParser(prog="agent-office native")
    parser.add_argument("--server", default=f"http://{host}:{settings.server.port}")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    bind = commands.add_parser("bind")
    bind.add_argument("agent_id")
    bind.add_argument("thread_id")
    bind.add_argument("--child-definition")
    reconnect = commands.add_parser("reconnect")
    reconnect.add_argument("agent_id")
    validate = commands.add_parser("validate")
    validate.add_argument("--thread")
    validate.add_argument("--codex-binary", default="codex")
    args = parser.parse_args(argv)
    if args.command == "validate":
        report = asyncio.run(validate_runtime(args.codex_binary, args.thread))
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report.get("health") == "connected" else 1)
    try:
        with httpx.Client(base_url=local_server(args.server), timeout=10) as client:
            if args.command == "status":
                response = client.get("/api/native/codex")
            elif args.command == "reconnect":
                response = client.post(
                    f"/api/native/codex/reconnect/{quote(args.agent_id, safe='')}"
                )
            else:
                agent = client.get(f"/api/agents/{quote(args.agent_id, safe='')}")
                agent.raise_for_status()
                response = client.post(
                    "/api/native/codex/bind",
                    json={
                        "office_agent_id": args.agent_id,
                        "thread_id": str(UUID(args.thread_id)),
                        "expected_generation": agent.json()["started_at"],
                        "child_definition_id": args.child_definition,
                    },
                )
            response.raise_for_status()
            print(json.dumps(response.json(), indent=2))
    except (httpx.HTTPError, ValueError, KeyError, OSError):
        parser.error("Local native request failed; check native status and explicit IDs")
