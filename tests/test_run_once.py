from __future__ import annotations

import sys
from pathlib import Path

from agent_template.models import ArtifactRef, CheckResult, MilestoneResult, ServiceHandle
from agent_template.runtime.run_once import RunOnceRequest, run_once


class FakeRunner:
    def __init__(self, artifact_store, run_id: str) -> None:
        self.artifact_store = artifact_store
        self.run_id = run_id
        self.closed = False
        self.started_with: bool | None = None

    def start(self, headless: bool = True) -> None:
        self.started_with = headless

    def close(self) -> None:
        self.closed = True


class FakeVerifier:
    def __init__(self, runner, milestone_path: Path) -> None:
        self.runner = runner
        self.milestone_path = milestone_path

    def verify(self, milestone_id: str, url: str) -> MilestoneResult:
        screenshot = self.runner.artifact_store.write_text(
            self.runner.run_id,
            'screenshot',
            f'{milestone_id}.png',
            'fake screenshot',
            label=milestone_id,
        )
        return MilestoneResult(
            milestone_id=milestone_id,
            passed=True,
            score=1.0,
            summary='shell boot passed',
            checks=[CheckResult(name='desktop_root', passed=True, evidence=url)],
            artifacts=[screenshot],
        )


def test_run_once_persists_state_and_result_in_per_run_layout(tmp_path: Path, monkeypatch) -> None:
    import agent_template.runtime.run_once as run_once_module

    monkeypatch.setattr(run_once_module, 'PlaywrightRunner', FakeRunner)
    monkeypatch.setattr(run_once_module, 'DesktopShellVerifier', FakeVerifier)

    request = RunOnceRequest(
        milestone_id='shell_boot',
        repo_path=tmp_path,
        state_path=tmp_path / 'state.json',
        artifacts_path=tmp_path / 'artifacts',
        milestone_file=tmp_path / 'desktop_shell.yaml',
        url='http://127.0.0.1:9999',
        headless=True,
    )

    outcome = run_once(request)

    assert outcome.exit_code == 0
    assert outcome.result.passed is True
    assert outcome.run_dir == tmp_path / 'artifacts' / 'runs' / outcome.state.run_id
    assert (outcome.run_dir / 'state.json').exists()
    assert (outcome.run_dir / 'result.json').exists()
    assert (outcome.run_dir / 'screenshot' / 'shell_boot.png').exists()
    assert Path(request.state_path).exists()


def test_run_once_boot_failure_captures_logs_and_skips_browser_checks(tmp_path: Path, monkeypatch) -> None:
    import agent_template.runtime.run_once as run_once_module

    class UnexpectedRunner:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError('browser checks should be skipped when boot fails')

    monkeypatch.setattr(run_once_module, 'PlaywrightRunner', UnexpectedRunner)

    request = RunOnceRequest(
        milestone_id='shell_boot',
        repo_path=tmp_path,
        state_path=tmp_path / 'state.json',
        artifacts_path=tmp_path / 'artifacts',
        milestone_file=tmp_path / 'desktop_shell.yaml',
        boot_command=(
            sys.executable,
            '-c',
            "import sys; print('booting'); print('boom', file=sys.stderr); raise SystemExit(3)",
        ),
        boot_cwd=tmp_path,
    )

    outcome = run_once(request)

    assert outcome.exit_code == 1
    assert outcome.result.passed is False
    assert outcome.result.checks == []
    assert (outcome.run_dir / 'logs' / 'target.stdout.log').read_text(encoding='utf-8').strip() == 'booting'
    assert 'boom' in (outcome.run_dir / 'logs' / 'target.stderr.log').read_text(encoding='utf-8')
    assert outcome.state.last_reflection is not None
    assert any('boom' in item for item in outcome.state.last_reflection.observed_evidence)


def test_run_once_stops_started_services_deterministically(tmp_path: Path, monkeypatch) -> None:
    import agent_template.runtime.run_once as run_once_module

    events: list[tuple[str, str]] = []

    class FakeProcessManager:
        def __init__(self, artifact_store, run_id: str) -> None:
            self.artifact_store = artifact_store
            self.run_id = run_id

        def start_service(self, name: str, command: list[str], cwd: Path, env=None) -> ServiceHandle:
            events.append(('start', name))
            log_dir = self.artifact_store.root / 'runs' / self.run_id / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            stdout = log_dir / f'{name}.stdout.log'
            stderr = log_dir / f'{name}.stderr.log'
            stdout.write_text('', encoding='utf-8')
            stderr.write_text('', encoding='utf-8')
            return ServiceHandle(
                name=name,
                pid=12345,
                command=command,
                cwd=str(cwd),
                started_at='now',
                stdout_artifact=ArtifactRef(kind='stdout', path=str(stdout), label=f'{name}-stdout'),
                stderr_artifact=ArtifactRef(kind='stderr', path=str(stderr), label=f'{name}-stderr'),
            )

        def stop_service(self, name: str) -> None:
            events.append(('stop', name))

    monkeypatch.setattr(run_once_module, 'ProcessManager', FakeProcessManager)
    monkeypatch.setattr(run_once_module, 'PlaywrightRunner', FakeRunner)
    monkeypatch.setattr(run_once_module, 'DesktopShellVerifier', FakeVerifier)
    monkeypatch.setattr(run_once_module, 'wait_for_url', lambda *args, **kwargs: True)

    request = RunOnceRequest(
        milestone_id='shell_boot',
        repo_path=tmp_path,
        state_path=tmp_path / 'state.json',
        artifacts_path=tmp_path / 'artifacts',
        milestone_file=tmp_path / 'desktop_shell.yaml',
        boot_command=('serve',),
        boot_cwd=tmp_path,
    )

    outcome = run_once(request)

    assert outcome.exit_code == 0
    assert events == [('start', 'target'), ('stop', 'target')]


def test_run_once_repeated_no_improvement_failure_tracks_stall_and_work_package(tmp_path: Path, monkeypatch) -> None:
    import json
    import agent_template.runtime.run_once as run_once_module

    class FailingVerifier:
        scores = [0.5, 0.5, 0.5]

        def __init__(self, runner, milestone_path: Path) -> None:
            self.runner = runner
            self.milestone_path = milestone_path

        def verify(self, milestone_id: str, url: str) -> MilestoneResult:
            score = self.scores.pop(0)
            return MilestoneResult(
                milestone_id=milestone_id,
                passed=False,
                score=score,
                summary='shell boot failed',
                checks=[CheckResult(name='taskbar', passed=False, evidence='missing taskbar')],
                artifacts=[],
            )

    monkeypatch.setattr(run_once_module, 'PlaywrightRunner', FakeRunner)
    monkeypatch.setattr(run_once_module, 'DesktopShellVerifier', FailingVerifier)

    request = RunOnceRequest(
        milestone_id='shell_boot',
        repo_path=tmp_path,
        state_path=tmp_path / 'state.json',
        artifacts_path=tmp_path / 'artifacts',
        milestone_file=tmp_path / 'desktop_shell.yaml',
        url='http://127.0.0.1:9999',
    )

    first = run_once(request)
    second = run_once(request)
    third = run_once(request)

    assert first.exit_code == 1
    assert second.state.no_progress_count == 1
    assert third.state.no_progress_count == 2
    assert third.state.last_reflection is not None
    assert third.state.last_reflection.classification == 'stalled_progress'
    assert third.state.last_reflection.issue_kind == 'code'
    assert any('0.5' in item for item in third.state.last_reflection.changed_since_last_attempt)

    reflection_payload = json.loads((third.run_dir / 'reflection.json').read_text(encoding='utf-8'))
    work_package_payload = json.loads((third.run_dir / 'work-package.json').read_text(encoding='utf-8'))

    assert reflection_payload['classification'] == 'stalled_progress'
    assert work_package_payload['goal'] == 'Make shell_boot pass on the next attempt'
    assert 'src/agent_template' in work_package_payload['read_files']


def test_run_once_improved_failure_resets_no_progress_count(tmp_path: Path, monkeypatch) -> None:
    import agent_template.runtime.run_once as run_once_module

    class ImprovingVerifier:
        scores = [0.25, 0.75]

        def __init__(self, runner, milestone_path: Path) -> None:
            self.runner = runner
            self.milestone_path = milestone_path

        def verify(self, milestone_id: str, url: str) -> MilestoneResult:
            score = self.scores.pop(0)
            return MilestoneResult(
                milestone_id=milestone_id,
                passed=False,
                score=score,
                summary='shell boot failed',
                checks=[CheckResult(name='taskbar', passed=False, evidence=f'score {score}')],
                artifacts=[],
            )

    monkeypatch.setattr(run_once_module, 'PlaywrightRunner', FakeRunner)
    monkeypatch.setattr(run_once_module, 'DesktopShellVerifier', ImprovingVerifier)

    request = RunOnceRequest(
        milestone_id='shell_boot',
        repo_path=tmp_path,
        state_path=tmp_path / 'state.json',
        artifacts_path=tmp_path / 'artifacts',
        milestone_file=tmp_path / 'desktop_shell.yaml',
        url='http://127.0.0.1:9999',
    )

    first = run_once(request)
    second = run_once(request)

    assert first.exit_code == 1
    assert second.exit_code == 1
    assert second.state.no_progress_count == 0
    assert second.state.last_reflection is not None
    assert second.state.last_reflection.classification == 'implementation_bug'
