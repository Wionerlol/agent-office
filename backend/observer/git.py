from dataclasses import dataclass
from pathlib import Path

from git import InvalidGitRepositoryError, NoSuchPathError, Repo


@dataclass(frozen=True)
class GitSnapshot:
    branch: str | None
    worktree: str
    changed_files: list[str]


class GitObserver:
    """Return a compact repository snapshot without leaking GitPython to callers."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path).resolve()

    def snapshot(self) -> GitSnapshot:
        try:
            repo = Repo(self.path, search_parent_directories=True)
        except (InvalidGitRepositoryError, NoSuchPathError):
            return GitSnapshot(branch=None, worktree=str(self.path), changed_files=[])

        try:
            branch = repo.active_branch.name
        except TypeError:
            branch = repo.head.commit.hexsha[:12] if repo.head.is_valid() else None

        changed = {item.a_path for item in repo.index.diff(None)}
        changed.update(item.a_path for item in repo.index.diff("HEAD"))
        changed.update(repo.untracked_files)
        worktree = repo.working_tree_dir or str(self.path)
        return GitSnapshot(branch=branch, worktree=worktree, changed_files=sorted(changed))
