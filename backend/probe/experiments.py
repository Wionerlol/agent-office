"""Opt-in real-runtime experiments. Unit fixtures never establish provider capability."""

import asyncio
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from backend.observer.tools import ToolObserver
from backend.probe.record import ProbeRecorder, private_output
from backend.probe.rpc import RpcClient

PROMPTS = {
    "A": "Read calc.py and README.md with a shell tool and explain answer in one sentence. "
    "Do not change files.",
    "B": "Use apply_patch to change calc.py answer from 41 to 42. Do not use shell redirection "
    "or Python for editing. Do not change other files. Briefly confirm.",
    "D": "Plan the next change to answer. The user has not decided whether the required result "
    "should be 43 or 44. Use request_user_input to ask for that contract choice before "
    "planning implementation. Do not guess or edit files.",
    "E": "Explicitly delegate a small read-only review of calc.py to one subagent using native "
    "spawn_agent. Request a reviewer role if supported; otherwise use a supported role. "
    "Wait for completion and report the result briefly. Do not substitute an OS subprocess "
    "or pretend delegation occurred.",
}


def create_workspace(output_dir: Path, scenarios: list[str]) -> Path:
    # All fixtures are owned by this run; never prompt a model against the user's checkout.
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    root = Path(tempfile.mkdtemp(prefix="agent-office-probe-"))
    (root / "calc.py").write_text("def answer():\n    return 41\n")
    (root / "README.md").write_text("A controlled arithmetic module.\n")
    expected = 42 if "B" in scenarios else 41
    (root / "test_calc.py").write_text(
        "import time\nfrom calc import answer\ndef test_answer():\n"
        f"    time.sleep(0.4)\n    assert answer() == {expected}\n"
    )
    (root / "AGENTS.md").write_text(
        "Controlled local runtime probe. Work only here. No remote MCP, web, browser, external "
        "messages, credentials or environment dumps. Follow the requested scenario exactly.\n"
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Probe",
            "-c",
            "user.email=probe@example.invalid",
            "commit",
            "-qm",
            "Initialize controlled fixture",
        ],
        check=True,
    )
    with private_output(output_dir / "workspace.txt") as output:
        output.write(str(root))
    return root


async def run_turn(
    client: RpcClient,
    thread: str,
    model: str,
    scenario: str,
    prompt: str,
) -> dict[str, Any]:
    while not client.events.empty():
        client.events.get_nowait()
    params: dict[str, Any] = {
        "threadId": thread,
        "input": [{"type": "text", "text": prompt}],
        "effort": "medium",
        "collaborationMode": {
            "mode": "plan" if scenario == "D" else "default",
            "settings": {
                "model": model,
                "reasoning_effort": "medium",
                "developer_instructions": None,
            },
        },
    }
    await client.request("turn/start", params)
    methods: Counter[str] = Counter()
    items: Counter[str] = Counter()
    input_requested = False
    async with asyncio.timeout(180):
        while True:
            event = await client.events.get()
            method = event["method"]
            methods[method] += 1
            body = event.get("params", {})
            item = body.get("item")
            if isinstance(item, dict):
                items[item["type"]] += 1
            if method == "item/tool/requestUserInput":
                input_requested = True
                # The harness answers this fixture's arithmetic choice only, after an observed wait.
                await asyncio.sleep(2)
                answers = {
                    question["id"]: {"answers": [question["options"][0]["label"]]}
                    for question in body["questions"]
                }
                await client.send({"id": event["id"], "result": {"answers": answers}})
            elif method in {
                "item/commandExecution/requestApproval",
                "item/fileChange/requestApproval",
            }:
                await client.send({"id": event["id"], "result": {"decision": "decline"}})
            if method == "turn/completed" and body.get("threadId") == thread:
                return {
                    "scenario": scenario,
                    "turn_status": body["turn"]["status"],
                    "input_request": input_requested,
                    "methods": dict(methods),
                    "items": dict(items),
                }


async def run_experiments(output_dir: Path, codex: str, scenarios: list[str]) -> None:
    scenarios = [name for name in "ABCDE" if name in scenarios]
    root = await asyncio.to_thread(create_workspace, output_dir, scenarios)
    with private_output(output_dir / "native.jsonl") as output:
        recorder = ProbeRecorder(output, "codex-app-server", root)
        children: set[str] = set()

        def receive(event: dict[str, Any]) -> None:
            recorder.record(event)
            item = event.get("params", {}).get("item", {})
            if isinstance(item, dict) and isinstance(item.get("agentThreadId"), str):
                children.add(item["agentThreadId"])

        async with RpcClient([codex, "app-server", "--listen", "stdio://"], receive) as client:
            await client.initialize()
            result = await client.request(
                "thread/start",
                {
                    "cwd": str(root),
                    "approvalPolicy": "never",
                    "sandbox": "workspace-write",
                    "developerInstructions": (
                        "Controlled local probe; no remote tools or credentials."
                    ),
                    "experimentalRawEvents": False,
                },
            )
            thread = result["thread"]["id"]
            recorder.record(
                {
                    "method": "probe.thread/start.response",
                    "params": {
                        "thread": result["thread"],
                    },
                }
            )
            observer = ToolObserver()
            with private_output(output_dir / "tool-process.jsonl") as tools:
                tool_recorder = ProbeRecorder(tools, "tool-process", root)
                stop = asyncio.Event()

                async def poll() -> None:
                    assert client.process is not None
                    while not stop.is_set():
                        events = await asyncio.to_thread(
                            observer.scan, "probe-parent", client.process.pid
                        )
                        for event in events:
                            tool_recorder.record(event.model_dump(mode="json"))
                        await asyncio.sleep(0.01)

                task = asyncio.create_task(poll())
                try:
                    for name in scenarios:
                        prompt = PROMPTS.get(name) or (
                            "Run each command separately with the shell tool: "
                            "rg -n answer calc.py; "
                            f"printf probe-shell; {sys.executable} -m pytest -q test_calc.py. "
                            "Report success briefly. Do not edit files."
                        )
                        summary = await run_turn(client, thread, result["model"], name, prompt)
                        print(json.dumps(summary), flush=True)
                        if summary["turn_status"] != "completed":
                            raise RuntimeError("A real provider turn did not complete")
                    for child in children:
                        metadata = await client.request(
                            "thread/read",
                            {
                                "threadId": child,
                                "includeTurns": False,
                            },
                        )
                        recorder.record({"method": "probe.child.metadata", "params": metadata})
                finally:
                    stop.set()
                    await task
