from __future__ import annotations

import json
from pathlib import Path

from ..models import RunState


class StateStore:
    """Persists run state as JSON for recovery and orchestration."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: RunState) -> None:
        self.path.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def load(self) -> RunState:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return RunState.model_validate(data)
