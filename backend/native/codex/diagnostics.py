"""Safe compatibility checks for already-loaded threads; no runtime control or raw output."""

from backend.native.codex.profiles import profile_for
from backend.native.codex.protocol import NativeUnavailable, ThreadMetadata
from backend.native.codex.transport import ReadOnlyClient, discover


async def validate_runtime(codex: str = "codex", thread: str | None = None) -> dict[str, object]:
    report: dict[str, object] = {
        "provider": "codex",
        "version": None,
        "protocol": "unknown",
        "checks": [],
    }
    checks: list[str] = []
    stage = "discovery"
    try:
        version, socket = await discover(codex)
        report["version"] = version
        profile = profile_for(version)
        report["protocol"] = "supported" if profile else "unsupported"
        checks.append("discovery")
        if profile is None:
            report["review_required"] = True
            return report
        stage = "initialize"

        async def ignore(_: dict[str, object]) -> None:
            pass

        async with ReadOnlyClient(socket, version, ignore) as client:
            checks.append("initialize")
            if thread:
                stage = "thread/read"
                metadata = ThreadMetadata.parse(
                    (await client.request(stage, {"threadId": thread, "includeTurns": False}))[
                        "thread"
                    ]
                )
                if metadata.thread != thread:
                    raise NativeUnavailable("Thread identity mismatch")
                checks.append(stage)
                stage = "thread/resume"
                resumed = await client.request(stage, {"threadId": thread, "excludeTurns": True})
                resumed_metadata = ThreadMetadata.parse(resumed["thread"], profile)
                if resumed_metadata.thread != thread:
                    raise NativeUnavailable("Subscription identity mismatch")
                checks.append(stage)
                stage = "thread/turns/list"
                turns = await client.request(
                    stage, {"threadId": thread, "limit": 1, "itemsView": "notLoaded"}
                )
                data = turns.get("data")
                if not isinstance(data, list):
                    raise NativeUnavailable("Invalid turn page")
                checks.append(stage)
                if data:
                    turn = data[0]
                    if (
                        not isinstance(turn, dict)
                        or not isinstance(turn.get("id"), str)
                        or turn.get("status") not in profile.turn_states
                    ):
                        raise NativeUnavailable("Invalid turn shape")
                    stage = "thread/items/list"
                    items = await client.request(
                        stage, {"threadId": thread, "turnId": turn["id"], "limit": 1}
                    )
                    entries = items.get("data")
                    if not isinstance(entries, list) or any(
                        not isinstance(entry, dict)
                        or not isinstance(entry.get("item"), dict)
                        or not isinstance(entry["item"].get("id"), str)
                        for entry in entries
                    ):
                        raise NativeUnavailable("Invalid item page")
                    checks.append(stage)
        report["health"] = "connected"
        report["schema"] = profile.schema
    except Exception:
        report["health"] = "unavailable"
        report["failed_check"] = stage
    finally:
        report["checks"] = checks
    return report
