from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import ArtifactRef


class ArtifactStore:
    """Stores run artifacts under a structured directory tree."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        path = self.root / 'runs' / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def run_path(self, run_id: str, relative_path: str | Path) -> Path:
        path = self.run_dir(run_id) / Path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _target_path(self, run_id: str, kind: str, filename: str) -> Path:
        target = self.run_dir(run_id) / kind
        target.mkdir(parents=True, exist_ok=True)
        return target / filename

    def write_text(
        self,
        run_id: str,
        kind: str,
        filename: str,
        content: str,
        label: str | None = None,
    ) -> ArtifactRef:
        path = self._target_path(run_id, kind, filename)
        path.write_text(content, encoding='utf-8')
        return ArtifactRef(kind=kind, path=str(path), label=label)

    def write_json(
        self,
        run_id: str,
        filename: str,
        payload: dict[str, Any],
        label: str | None = None,
    ) -> ArtifactRef:
        path = self._target_path(run_id, 'json', filename)
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return ArtifactRef(kind='json', path=str(path), label=label)

    def write_run_json(
        self,
        run_id: str,
        filename: str,
        payload: dict[str, Any],
        label: str | None = None,
    ) -> ArtifactRef:
        path = self.run_path(run_id, filename)
        path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        return ArtifactRef(kind='json', path=str(path), label=label)

    def write_run_text(
        self,
        run_id: str,
        relative_path: str,
        content: str,
        kind: str = 'text',
        label: str | None = None,
    ) -> ArtifactRef:
        path = self.run_path(run_id, relative_path)
        path.write_text(content, encoding='utf-8')
        return ArtifactRef(kind=kind, path=str(path), label=label)

    def register_file(
        self,
        run_id: str,
        kind: str,
        source_path: Path,
        label: str | None = None,
    ) -> ArtifactRef:
        target = self._target_path(run_id, kind, source_path.name)
        target.write_bytes(source_path.read_bytes())
        return ArtifactRef(kind=kind, path=str(target), label=label)
