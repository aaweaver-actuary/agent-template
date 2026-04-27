from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import TextIO

from ..config import Config
from ..models import ArtifactRef, CommandResult, ServiceHandle
from ..runtime.artifact_store import ArtifactStore

cfg = Config()


class ProcessManager:
    """Runs commands and manages long-lived services."""

    def __init__(self, artifact_store: ArtifactStore, run_id: str) -> None:
        self.artifact_store = artifact_store
        self.run_id = run_id
        self._services: dict[str, subprocess.Popen[str]] = {}
        self._service_streams: dict[str, tuple[TextIO, TextIO]] = {}

    @property
    def ast(self) -> ArtifactStore:
        """Alias for the artifact store."""
        return self.artifact_store

    def run(
        self,
        command: list[str],
        cwd: Path,
        timeout_s: int = 120,
        env: dict[str, str] | None = None,
        measure_duration: bool = True,
    ) -> CommandResult:
        """Run a command in a subprocess and return the result."""
        started_at = cfg.now()
        if measure_duration:
            started = time.perf_counter()

        proc = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env={**os.environ, **(env or {})},
            check=False,
        )

        finished_at = cfg.now()
        if measure_duration:
            duration = time.perf_counter() - started
        else:
            duration = 0.0

        return CommandResult(
            command=command,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            started_at=started_at,
            finished_at=finished_at,
            duration_seconds=duration,
            cwd=str(cwd),
        )

    def start_service(
        self,
        name: str,
        command: list[str],
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> ServiceHandle:
        """Start a long-lived service and return a handle to it."""
        stdout_path = self.ast.run_path(self.run_id, f'logs/{name}.stdout.log')
        stderr_path = self.ast.run_path(self.run_id, f'logs/{name}.stderr.log')
        stdout_file = stdout_path.open('w', encoding='utf-8')
        stderr_file = stderr_path.open('w', encoding='utf-8')

        proc = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            env={**os.environ, **(env or {})},
        )

        self._services[name] = proc
        self._service_streams[name] = (stdout_file, stderr_file)

        stdout_artifact = ArtifactRef(
            kind='stdout',
            path=str(stdout_path),
            label=f'{name}-stdout',
        )
        stderr_artifact = ArtifactRef(
            kind='stderr',
            path=str(stderr_path),
            label=f'{name}-stderr',
        )

        return ServiceHandle(
            name=name,
            pid=proc.pid,
            command=command,
            cwd=str(cwd),
            started_at=cfg.now(),
            stdout_artifact=stdout_artifact,
            stderr_artifact=stderr_artifact,
        )

    def service_exit_code(self, name: str) -> int | None:
        proc = self._services.get(name)
        if proc is None:
            return None
        return proc.poll()

    def stop_service(self, name: str) -> None:
        """Stop a long-lived service by name."""
        proc = self._services.get(name)
        streams = self._service_streams.get(name)
        if proc is None:
            return

        if proc.poll() is None:
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            except ProcessLookupError:
                pass
        else:
            proc.wait(timeout=1)

        if streams is not None:
            for handle in streams:
                handle.close()

        self._services.pop(name, None)
        self._service_streams.pop(name, None)

    def stop_all(self) -> None:
        for name in list(self._services):
            self.stop_service(name)
