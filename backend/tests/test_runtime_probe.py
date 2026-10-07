"""Transport/safety tests only; these fixtures make no provider capability claims."""

import asyncio
import io
import json
import stat
import sys
from pathlib import Path

import pytest

from backend.probe.__main__ import main
from backend.probe.observe import ThreadScope
from backend.probe.record import ProbeRecorder, opaque_id, private_output
from backend.probe.rpc import RpcClient


def recorder(tmp_path: Path, source: str = "codex-app-server") -> ProbeRecorder:
    return ProbeRecorder(io.StringIO(), source, tmp_path)


@pytest.mark.parametrize(
    "source,events",
    [
        (
            "codex-exec",
            [
                {"type": "thread.started", "thread_id": "parent"},
                {"type": "item.started", "item": {"id": "item-1", "type": "command_execution"}},
            ],
        ),
        (
            "codex-rollout",
            [
                {
                    "type": "session_meta",
                    "timestamp": "2026-10-02T10:00:00Z",
                    "ordinal": 17,
                    "payload": {"id": "parent"},
                },
                {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-1"}},
            ],
        ),
        (
            "codex-app-server",
            [
                {
                    "method": "turn/started",
                    "params": {"threadId": "parent", "turn": {"id": "turn-1"}},
                },
                {
                    "method": "item/started",
                    "params": {"threadId": "parent", "item": {"type": "reasoning"}},
                },
            ],
        ),
    ],
)
def test_structured_sources_preserve_order_type_and_identity(
    tmp_path: Path,
    source: str,
    events: list[dict[str, object]],
) -> None:
    capture = recorder(tmp_path, source)
    records = [capture.line(json.dumps(event)) for event in events]
    assert [record["sequence"] for record in records] == [1, 2]
    assert [record["raw_type"] for record in records] == [
        event.get("method", event.get("type")) for event in events
    ]
    assert all(record["session_id"] == opaque_id("parent") for record in records)
    assert records[0]["timestamp"] <= records[1]["timestamp"]
    if source == "codex-rollout":
        assert records[0]["provider_timestamp"] == "2026-10-02T10:00:00Z"
        assert records[0]["provider_sequence"] == 17


def test_nested_status_patch_and_parent_metadata_are_not_flattened(tmp_path: Path) -> None:
    value = {
        "method": "item/started",
        "params": {
            "threadId": "parent",
            "item": {
                "type": "fileChange",
                "prompt": None,
                "summary": [],
                "changes": [
                    {
                        "path": str(tmp_path / "calc.py"),
                        "kind": {"type": "update"},
                        "diff": "private code",
                    }
                ],
            },
            "thread": {
                "id": "child",
                "parentThreadId": "parent",
                "agentRole": None,
                "agentNickname": "Linnaeus",
                "source": {
                    "subAgent": {
                        "thread_spawn": {
                            "parent_thread_id": "parent",
                            "depth": 1,
                        }
                    }
                },
                "status": {"type": "active", "activeFlags": ["waitingOnUserInput"]},
            },
        },
    }
    result = recorder(tmp_path).record(value)["payload"]
    assert result["thread"]["parentThreadId"] == result["threadId"]
    assert result["thread"]["agentRole"] is None
    assert result["item"]["prompt"] is None
    assert result["item"]["summary"] == []
    assert result["thread"]["status"] == {"type": "active", "activeFlags": ["waitingOnUserInput"]}
    assert result["thread"]["source"]["subAgent"]["thread_spawn"]["depth"] == 1
    assert result["item"]["changes"] == [
        {
            "path": "calc.py",
            "kind": {"type": "update"},
            "diff": "[redacted]",
        }
    ]


def test_request_and_resolution_identifiers_correlate(tmp_path: Path) -> None:
    capture = recorder(tmp_path)
    requested = capture.record(
        {
            "id": 12,
            "method": "item/tool/requestUserInput",
            "params": {
                "threadId": "parent",
                "itemId": "item-1",
                "questions": [{"id": "q", "question": "private"}],
            },
        }
    )
    resolved = capture.record(
        {
            "method": "serverRequest/resolved",
            "params": {
                "threadId": "parent",
                "requestId": 12,
            },
        }
    )
    assert requested["request_id"] == resolved["payload"]["requestId"]
    assert requested["payload"]["questions"][0]["question"] == "[redacted]"


def test_deny_content_credentials_unknown_fields_and_external_paths(tmp_path: Path) -> None:
    capture = recorder(tmp_path)
    value = {
        "method": "item/completed",
        "params": {
            "threadId": "sk-private-key",
            "item": {
                "type": "mcpToolCall",
                "id": "bearer-private-id",
                "tool": "safe_tool",
                "arguments": {"api_key": "sk-private-key", "prompt": "unrelated user content"},
                "result": {
                    "content": "unrelated user content",
                    "headers": {"Authorization": "Bearer raw"},
                },
                "status": "completed",
                "command": "echo sk-private-key",
                "path": "/private/credential",
            },
            "environment": {"PASSWORD": "very-private"},
            "preview": "unrelated user content",
            "thread": {"name": "unrelated user content", "agentRole": "sk-private-key"},
        },
    }
    record = capture.record(value)
    rendered = json.dumps(record)
    for content in (
        "sk-private-key",
        "bearer-private-id",
        "unrelated user content",
        "very-private",
        "Bearer raw",
        "Authorization",
        "environment",
        "/private/credential",
    ):
        assert content not in rendered
    assert record["payload"]["item"]["command"] == {
        "redacted": True,
        "executable_tokens": ["echo"],
    }
    assert record["payload"]["item"]["path"] == "[outside-workspace]"


@pytest.mark.parametrize(
    "line",
    [
        "not JSON with sk-secret",
        "null",
        "[]",
        "123",
        '{"method": {"password": "secret"}}',
        '{"type":"session_meta","payload":null}',
        '{"type":"x","timestamp":"sk-secret"}',
        '{"type":"x","durationMs":NaN}',
        '{"type":"x","name":["private"]}',
    ],
)
def test_malformed_and_unexpected_shapes_do_not_leak_or_abort(tmp_path: Path, line: str) -> None:
    capture = recorder(tmp_path)
    capture.line(line)
    record = capture.line('{"type":"turn.completed"}')
    assert record["sequence"] == 2
    assert "sk-secret" not in capture.output.getvalue()
    assert "NaN" not in capture.output.getvalue()


def test_parent_scope_discovers_native_children_but_excludes_other_sessions(tmp_path: Path) -> None:
    capture = recorder(tmp_path)
    scope = ThreadScope("parent", capture)
    scope.receive({"method": "thread/started", "params": {"thread": {"parentThreadId": {}}}})
    scope.receive({"method": "thread/started", "params": None})
    scope.receive(
        {
            "method": "item/started",
            "params": {
                "threadId": "unrelated",
                "item": {"type": "userMessage", "content": "private"},
            },
        }
    )
    scope.receive(
        {
            "method": "item/started",
            "params": {
                "threadId": "parent",
                "item": {"type": "subAgentActivity", "agentThreadId": "child"},
            },
        }
    )
    scope.receive(
        {
            "method": "turn/completed",
            "params": {"threadId": "child", "turn": {"status": "completed"}},
        }
    )
    assert capture.sequence == 2
    assert scope.threads == {"parent", "child"}
    assert "unrelated" not in capture.output.getvalue()
    assert "private" not in capture.output.getvalue()


def test_output_is_private_and_never_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "runtime" / "probe" / "events.jsonl"
    with private_output(path) as output:
        output.write("fixture\n")
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        private_output(path)
    assert path.read_text() == "fixture\n"


def test_cli_source_unavailable_reports_no_sensitive_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(
            [
                "capture",
                "--source",
                "codex-exec",
                "--workspace",
                str(tmp_path),
                "--input",
                str(tmp_path / "sk-private-input"),
                "--output",
                str(tmp_path / "probe.jsonl"),
            ]
        )
    assert stopped.value.code == 2
    assert capsys.readouterr().err == "Probe unavailable: FileNotFoundError\n"


@pytest.mark.asyncio
async def test_missing_native_binary_is_an_environment_failure() -> None:
    with pytest.raises(FileNotFoundError):
        async with RpcClient(["/not-installed/agent-office-codex"], lambda _: None):
            pass


@pytest.mark.asyncio
async def test_rpc_parser_and_disconnect_are_transport_checks_only(tmp_path: Path) -> None:
    script = tmp_path / "fixture.py"
    script.write_text(
        "import sys,json\n"
        "request=json.loads(sys.stdin.readline())\n"
        'print("invalid JSON",flush=True)\n'
        'print(json.dumps({"id":{},"result":{}}),flush=True)\n'
        'print(json.dumps({"id":request["id"],"result":{"ok":True}}),flush=True)\n'
    )
    events: list[dict[str, object]] = []
    async with RpcClient([sys.executable, str(script)], events.append) as client:
        assert await client.request("fixture/transport", {}) == {"ok": True}
        await asyncio.sleep(0.05)
        with pytest.raises((ConnectionError, BrokenPipeError)):
            await client.request("fixture/after-close", {})
    assert events == [{"type": "probe.malformed"}]


def test_unavailable_handshake_does_not_print_server_error_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import backend.probe.__main__ as probe_cli

    class ProtocolFailure(Exception):
        pass

    async def unavailable(*args: object) -> None:
        raise ProtocolFailure("server body contains sk-private-key")

    monkeypatch.setattr(probe_cli, "observe_thread", unavailable)
    with pytest.raises(SystemExit) as stopped:
        main(
            [
                "observe",
                "--socket",
                str(tmp_path / "socket"),
                "--thread",
                "parent",
                "--workspace",
                str(tmp_path),
                "--output",
                str(tmp_path / "probe.jsonl"),
            ]
        )
    assert stopped.value.code == 2
    assert capsys.readouterr().err == "Probe unavailable: ProtocolFailure\n"
