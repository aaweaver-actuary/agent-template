from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

from ..browser.playwright_runner import PlaywrightRunner
from ..ledger.reflection import (
    DEFAULT_BOOT_MODIFY_FILES,
    DEFAULT_VERIFY_MODIFY_FILES,
    build_reflection_record,
    build_work_package,
    classify_reflection_issue,
)
from ..ledger.state_store import StateStore
from ..models import ArtifactRef, MilestoneResult, ReflectionRecord, RunState, ServiceHandle, WorkPackage
from ..runtime.artifact_store import ArtifactStore
from ..runtime.process_manager import ProcessManager
from ..verifiers.desktop_shell import DEFAULT_MILESTONE_PATH, DesktopShellVerifier

DEFAULT_HARNESS_DIR = Path(__file__).resolve().parents[1] / 'harness' / 'desktop_shell'


@dataclass(frozen=True)
class RunOnceRequest:
    milestone_id: str
    repo_path: Path
    state_path: Path
    artifacts_path: Path
    milestone_file: Path = DEFAULT_MILESTONE_PATH
    url: str | None = None
    headless: bool = True
    boot_command: tuple[str, ...] | None = None
    boot_cwd: Path | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, 'repo_path', Path(self.repo_path))
        object.__setattr__(self, 'state_path', Path(self.state_path))
        object.__setattr__(self, 'artifacts_path', Path(self.artifacts_path))
        object.__setattr__(self, 'milestone_file', Path(self.milestone_file))
        if self.boot_cwd is not None:
            object.__setattr__(self, 'boot_cwd', Path(self.boot_cwd))


@dataclass(frozen=True)
class RunOnceOutcome:
    exit_code: int
    state: RunState
    result: MilestoneResult
    run_dir: Path


def load_previous_state(path: Path) -> RunState | None:
    if not path.exists():
        return None
    return StateStore(path).load()


def build_run_state(request: RunOnceRequest, previous_state: RunState | None) -> RunState:
    return RunState(
        objective=f'run once {request.milestone_id}',
        repo_path=str(request.repo_path),
        branch_id=previous_state.branch_id if previous_state is not None else 'main',
        milestone_id=request.milestone_id,
        no_progress_count=previous_state.no_progress_count if previous_state is not None else 0,
    )


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


def default_boot_command(port: int) -> tuple[str, ...]:
    return (
        sys.executable,
        '-m',
        'http.server',
        str(port),
        '--bind',
        '127.0.0.1',
    )


def wait_for_url(
    url: str,
    *,
    timeout_seconds: float,
    process_manager: ProcessManager | None = None,
    service_name: str | None = None,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process_manager is not None and service_name is not None:
            exit_code = process_manager.service_exit_code(service_name)
            if exit_code is not None:
                return False
        try:
            with urlopen(url, timeout=0.5) as response:
                if response.status < 500:
                    return True
        except URLError:
            pass
        time.sleep(0.1)
    return False


def service_artifacts(handle: ServiceHandle | None) -> list[ArtifactRef]:
    if handle is None:
        return []
    artifacts: list[ArtifactRef] = []
    if handle.stdout_artifact is not None:
        artifacts.append(handle.stdout_artifact)
    if handle.stderr_artifact is not None:
        artifacts.append(handle.stderr_artifact)
    return artifacts


def boot_failure_observations(handle: ServiceHandle | None) -> list[str]:
    if handle is None:
        return ['target process did not start']

    observations: list[str] = []
    for artifact in service_artifacts(handle):
        content = Path(artifact.path).read_text(encoding='utf-8').strip()
        if content:
            observations.append(content)
    if not observations:
        observations.append('target URL did not become ready before timeout')
    return observations


def build_boot_failure_result(request: RunOnceRequest, artifacts: list[ArtifactRef]) -> MilestoneResult:
    return MilestoneResult(
        milestone_id=request.milestone_id,
        passed=False,
        score=0.0,
        checks=[],
        summary='Target failed to boot',
        artifacts=artifacts,
    )


def detect_touched_files(repo_path: Path) -> list[str] | None:
    try:
        completed = subprocess.run(
            ['git', '-C', str(repo_path), 'status', '--short', '--untracked-files=all'],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    touched_files: list[str] = []
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        touched_files.append(stripped[3:] if len(stripped) > 3 else stripped)
    return touched_files


def compute_no_progress_count(
    previous_state: RunState | None,
    result: MilestoneResult,
    classification: str,
) -> int:
    if result.passed:
        return 0
    if previous_state is None or previous_state.current_score is None:
        return 0

    previous_score = previous_state.current_score
    previous_failed_checks = previous_state.last_reflection.failed_checks if previous_state.last_reflection is not None else []
    current_failed_checks = [check.name for check in result.checks if not check.passed]
    previous_classification = previous_state.last_reflection.classification if previous_state.last_reflection is not None else None

    if result.score > previous_score:
        return 0
    if current_failed_checks != previous_failed_checks:
        return 0
    if previous_classification is not None and classification != previous_classification and classification != 'stalled_progress':
        return 0
    return previous_state.no_progress_count + 1


def describe_attempt_change(
    previous_state: RunState | None,
    result: MilestoneResult,
    touched_files: list[str] | None,
) -> list[str]:
    changes: list[str] = []
    if previous_state is None or previous_state.current_score is None:
        changes.append('no previous attempt available')
    else:
        previous_score = previous_state.current_score
        if result.score > previous_score:
            changes.append(f'score improved from {previous_score} to {result.score}')
        elif result.score == previous_score:
            changes.append(f'score did not improve from {previous_score} to {result.score}')
        else:
            changes.append(f'score regressed from {previous_score} to {result.score}')

        previous_failed_checks = previous_state.last_reflection.failed_checks if previous_state.last_reflection is not None else []
        current_failed_checks = [check.name for check in result.checks if not check.passed]
        if current_failed_checks and current_failed_checks == previous_failed_checks:
            changes.append(f"failed checks unchanged: {', '.join(current_failed_checks)}")
        elif current_failed_checks:
            changes.append(f"failed checks changed to: {', '.join(current_failed_checks)}")

    if touched_files is None:
        changes.append('touched-file data unavailable; unable to compare changed files')
    elif not touched_files:
        changes.append('no touched files detected in the working tree')
    elif previous_state is None or not previous_state.touched_files:
        changes.append(f"current touched files: {', '.join(touched_files)}")
    elif set(touched_files) == set(previous_state.touched_files):
        changes.append(f"touched files unchanged: {', '.join(touched_files)}")
    else:
        changes.append(f"touched files changed to: {', '.join(touched_files)}")

    return changes


def build_failed_run_artifacts(
    *,
    request: RunOnceRequest,
    result: MilestoneResult,
    previous_state: RunState | None,
    touched_files: list[str] | None,
    trigger_type: str,
    observed_evidence: list[str] | None = None,
    next_strategy: list[str],
) -> tuple[ReflectionRecord, WorkPackage, int]:
    observations = observed_evidence or [
        check.evidence or f"check '{check.name}' failed"
        for check in result.checks
        if not check.passed
    ]
    failed_check_names = [check.name for check in result.checks if not check.passed]
    modify_files = DEFAULT_BOOT_MODIFY_FILES if trigger_type == 'boot_failure' else DEFAULT_VERIFY_MODIFY_FILES
    decision = classify_reflection_issue(
        trigger_type=trigger_type,
        failed_checks=failed_check_names,
        observed_evidence=observations,
        touched_files=touched_files,
        modify_files=modify_files,
        previous_failed_checks=previous_state.last_reflection.failed_checks if previous_state and previous_state.last_reflection else [],
        previous_touched_files=previous_state.touched_files if previous_state is not None else [],
        previous_observed_evidence=previous_state.last_reflection.observed_evidence if previous_state and previous_state.last_reflection else [],
    )
    no_progress_count = compute_no_progress_count(previous_state, result, decision.classification)
    changed_since_last_attempt = describe_attempt_change(previous_state, result, touched_files)

    reflection = build_reflection_record(
        trigger_type=trigger_type,
        slice_id='run-once',
        milestone_result=result,
        target=request.milestone_id,
        classification=decision.classification,
        issue_kind=decision.issue_kind,
        issue_subtype=decision.issue_subtype,
        changed_since_last_attempt=changed_since_last_attempt,
        touched_files=touched_files,
        no_progress_count=no_progress_count,
        next_strategy=next_strategy,
        durable_memory_candidate=decision.classification in {'stalled_progress', 'scope_delta'},
    )
    if observed_evidence is not None:
        reflection.observed_evidence = observations

    work_package = build_work_package(
        slice_id='run-once',
        milestone_id=request.milestone_id,
        milestone_file=request.milestone_file,
        classification=decision.classification,
        trigger_type=trigger_type,
        failed_checks=reflection.failed_checks,
    )
    return reflection, work_package, no_progress_count


def persist_run(
    request: RunOnceRequest,
    store: ArtifactStore,
    state: RunState,
    result: MilestoneResult,
) -> None:
    state_artifact = store.write_run_json(state.run_id, 'state.json', state.model_dump(), label='run-state')
    result_artifact = store.write_run_json(state.run_id, 'result.json', result.model_dump(), label='milestone-result')
    state.artifacts.extend([state_artifact, result_artifact])
    if state.last_reflection is not None:
        reflection_artifact = store.write_run_json(
            state.run_id,
            'reflection.json',
            state.last_reflection.model_dump(),
            label='reflection-record',
        )
        state.artifacts.append(reflection_artifact)
    if state.last_work_package is not None:
        work_package_artifact = store.write_run_json(
            state.run_id,
            'work-package.json',
            state.last_work_package.model_dump(),
            label='work-package',
        )
        state.artifacts.append(work_package_artifact)
        StateStore(request.state_path).save(state)
        return
    StateStore(request.state_path).save(state)


def run_once(request: RunOnceRequest) -> RunOnceOutcome:
    previous_state = load_previous_state(request.state_path)
    state = build_run_state(request, previous_state)
    current_touched_files = detect_touched_files(request.repo_path)
    state.touched_files = current_touched_files or []
    store = ArtifactStore(request.artifacts_path)
    process_manager = ProcessManager(store, state.run_id)
    run_dir = store.run_dir(state.run_id)
    runner: PlaywrightRunner | None = None
    service_name: str | None = None
    handle: ServiceHandle | None = None

    try:
        target_url = request.url
        if target_url is None:
            port = find_free_port()
            service_name = 'target'
            boot_command = request.boot_command or default_boot_command(port)
            boot_cwd = request.boot_cwd or DEFAULT_HARNESS_DIR
            handle = process_manager.start_service(service_name, list(boot_command), boot_cwd)
            target_url = f'http://127.0.0.1:{port}/'
            if not wait_for_url(
                target_url,
                timeout_seconds=10.0,
                process_manager=process_manager,
                service_name=service_name,
            ):
                artifacts = service_artifacts(handle)
                result = build_boot_failure_result(request, artifacts)
                reflection, work_package, no_progress_count = build_failed_run_artifacts(
                    request=request,
                    result=result,
                    previous_state=previous_state,
                    touched_files=current_touched_files,
                    trigger_type='boot_failure',
                    observed_evidence=boot_failure_observations(handle),
                    next_strategy=[
                        'inspect captured stdout and stderr',
                        'repair the target boot command before retrying browser checks',
                    ],
                )
                state.current_score = result.score
                state.no_progress_count = no_progress_count
                state.artifacts.extend(artifacts)
                state.last_reflection = reflection
                state.last_work_package = work_package
                persist_run(request, store, state, result)
                return RunOnceOutcome(exit_code=1, state=state, result=result, run_dir=run_dir)

        runner = PlaywrightRunner(store, state.run_id)
        runner.start(headless=request.headless)
        verifier = DesktopShellVerifier(runner, milestone_path=request.milestone_file)
        result = verifier.verify(request.milestone_id, target_url)
        state.current_score = result.score
        state.no_progress_count = 0
        state.artifacts.extend(result.artifacts)
        if not result.passed:
            reflection, work_package, no_progress_count = build_failed_run_artifacts(
                request=request,
                result=result,
                previous_state=previous_state,
                touched_files=current_touched_files,
                trigger_type='failed_verifier',
                next_strategy=[
                    'inspect failed selectors',
                    'inspect screenshot and browser errors',
                ],
            )
            state.no_progress_count = no_progress_count
            state.last_reflection = reflection
            state.last_work_package = work_package
        persist_run(request, store, state, result)
        return RunOnceOutcome(
            exit_code=0 if result.passed else 1,
            state=state,
            result=result,
            run_dir=run_dir,
        )
    finally:
        if runner is not None:
            runner.close()
        if service_name is not None:
            process_manager.stop_service(service_name)
