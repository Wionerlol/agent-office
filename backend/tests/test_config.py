from pathlib import Path

import pytest

import backend.config as config_module
from backend.config import Settings


def test_default_config_is_independent_of_the_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_config = Path(config_module.__file__).resolve().parents[1] / "config" / "office.yaml"
    expected = Settings.load(source_config)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_OFFICE_CONFIG", raising=False)

    actual = Settings.load_default()

    assert actual == expected
