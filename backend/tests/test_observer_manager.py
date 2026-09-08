import os
import subprocess
import sys
from pathlib import Path

import pytest

from backend.adapters.generic import GenericProcessAdapter
from backend.config import ObserverSettings
from backend.observer.manager import ObserverManager
from backend.runtime.office import OfficeRuntime


@pytest.mark.asyncio
async def test_manager_tracks_detected_process_until_it_exits(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "AGENT_OFFICE_ID": "managed-worker",
        "AGENT_OFFICE_NAME": "Managed Worker",
        "AGENT_OFFICE_PROVIDER": "custom",
        "AGENT_OFFICE_REPOSITORY": str(tmp_path),
    }
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"],
        env=environment,
    )
    runtime = OfficeRuntime()
    manager = ObserverManager(
        runtime,
        ObserverSettings(enabled=True, scan_interval=0.01),
        adapters=[GenericProcessAdapter(pids=[process.pid])],
    )
    try:
        await manager.run_once()
        assert runtime.registry.get("managed-worker").pid == process.pid

        process.terminate()
        process.wait(timeout=5)
        await manager.run_once()
        with pytest.raises(KeyError):
            runtime.registry.get("managed-worker")
    finally:
        if process.poll() is None:
            process.terminate()
