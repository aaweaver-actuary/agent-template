from __future__ import annotations

from pathlib import Path

from ..models import SnapshotRef
from ..runtime.process_manager import ProcessManager


class SnapshotManager:
    """Creates lightweight git-based checkpoints."""

    def __init__(self, process_manager: ProcessManager, repo_path: Path) -> None:
        self.process_manager = process_manager
        self.repo_path = repo_path

    def create(self, label: str) -> SnapshotRef:
        # Assumes repo is already initialized as git.
        self.process_manager.run(["git", "add", "-A"], cwd=self.repo_path, timeout_s=30)
        self.process_manager.run(
            ["git", "commit", "--allow-empty", "-m", f"checkpoint: {label}"],
            cwd=self.repo_path,
            timeout_s=30,
        )
        rev = self.process_manager.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            timeout_s=10,
        )
        return SnapshotRef(label=label, path=rev.stdout.strip())

    def restore(self, snapshot: SnapshotRef) -> None:
        self.process_manager.run(
            ["git", "reset", "--hard", snapshot.path],
            cwd=self.repo_path,
            timeout_s=30,
        )
