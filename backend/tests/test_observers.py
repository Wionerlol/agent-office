from pathlib import Path

from git import Repo

from backend.models import AgentEventType
from backend.observer.filesystem import FileSystemObserver
from backend.observer.git import GitObserver


def initialize_repo(path: Path) -> Repo:
    repo = Repo.init(path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Agent Office Test")
        config.set_value("user", "email", "agent-office@example.test")
    (path / "tracked.py").write_text("value = 1\n", encoding="utf-8")
    repo.index.add(["tracked.py"])
    repo.index.commit("Initial commit")
    return repo


def test_git_and_filesystem_observers_report_repository_changes(tmp_path):
    initialize_repo(tmp_path)
    git_observer = GitObserver(tmp_path)
    filesystem = FileSystemObserver(tmp_path)

    filesystem.scan("worker")
    (tmp_path / "tracked.py").write_text("value = 2\n", encoding="utf-8")
    (tmp_path / "created.ts").write_text("export {};\n", encoding="utf-8")

    snapshot = git_observer.snapshot()
    events = filesystem.scan("worker")

    assert snapshot.branch in {"master", "main"}
    assert snapshot.changed_files == ["created.ts", "tracked.py"]
    assert {event.type for event in events} == {AgentEventType.FILE_CHANGED}
    assert {event.payload["file"] for event in events} == {"created.ts", "tracked.py"}
