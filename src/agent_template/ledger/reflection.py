from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models import (
    IssueKind,
    IssueSubtype,
    MilestoneResult,
    ReflectionClassification,
    ReflectionRecord,
    WorkPackage,
)

DEFAULT_VERIFY_MODIFY_FILES = ['src/agent_template/harness/desktop_shell/index.html']
DEFAULT_BOOT_MODIFY_FILES = ['src/agent_template/runtime/run_once.py']


@dataclass(frozen=True)
class ReflectionIssue:
    classification: ReflectionClassification
    issue_kind: IssueKind
    issue_subtype: IssueSubtype


def _normalize_paths(paths: list[str] | None) -> list[str]:
    return sorted(dict.fromkeys(paths or []))


def _same_touched_files(current: list[str], previous: list[str]) -> bool:
    return bool(current) and bool(previous) and set(current) == set(previous)


def _joined_evidence(observed_evidence: list[str]) -> str:
    return ' '.join(observed_evidence).lower()


def classify_reflection_issue(
    *,
    trigger_type: str,
    failed_checks: list[str],
    observed_evidence: list[str],
    touched_files: list[str] | None,
    modify_files: list[str] | None,
    previous_failed_checks: list[str] | None,
    previous_touched_files: list[str] | None,
    previous_observed_evidence: list[str] | None = None,
) -> ReflectionIssue:
    current_touched_files = _normalize_paths(touched_files)
    previous_touched = _normalize_paths(previous_touched_files)
    allowed_modify_files = set(modify_files or [])
    text = _joined_evidence(observed_evidence)
    previous_text = _joined_evidence(previous_observed_evidence or [])

    if trigger_type == 'schema_error':
        return ReflectionIssue('schema_error', 'spec', 'schema_violation')

    if trigger_type == 'boot_failure':
        subtype: IssueSubtype = 'runtime_error'
        if any(token in text for token in ('network error', 'connection refused', 'connection reset', 'timed out')):
            subtype = 'network_error'
        return ReflectionIssue('boot_failure', 'code', subtype)

    if 'acceptance criteria stale' in text or 'stale acceptance' in text:
        return ReflectionIssue('verification_failure', 'spec', 'stale_acceptance_criteria')

    if 'selector mismatch' in text or 'selector is stale' in text:
        return ReflectionIssue('verification_failure', 'test', 'selector_mismatch')

    if (
        failed_checks
        and failed_checks == list(previous_failed_checks or [])
        and _same_touched_files(current_touched_files, previous_touched)
        and previous_text == text
    ):
        return ReflectionIssue('stalled_progress', 'code', 'same_files_same_failure')

    if current_touched_files and allowed_modify_files:
        if any(path not in allowed_modify_files for path in current_touched_files):
            return ReflectionIssue('scope_delta', 'scope', 'outside_work_package')

    return ReflectionIssue('verification_failure', 'code', 'missing_ui')


def _default_expected_evidence(trigger_type: str, target: str) -> list[str]:
    if trigger_type == 'boot_failure':
        return [f"target '{target}' should boot and serve the milestone URL"]
    if trigger_type == 'schema_error':
        return [f"manifest for '{target}' should validate against the schema"]
    return [f"milestone '{target}' should pass"]


def build_reflection_record(
    *,
    trigger_type: str,
    slice_id: str,
    milestone_result: MilestoneResult,
    target: str,
    classification: ReflectionClassification,
    issue_kind: IssueKind,
    issue_subtype: IssueSubtype,
    changed_since_last_attempt: list[str] | None = None,
    touched_files: list[str] | None = None,
    no_progress_count: int = 0,
    next_strategy: list[str],
    durable_memory_candidate: bool = False,
) -> ReflectionRecord:
    failed_checks = [check for check in milestone_result.checks if not check.passed]

    expected = [f"check '{check.name}' should pass" for check in failed_checks]
    observed = [check.evidence or f"check '{check.name}' failed" for check in failed_checks]
    if not expected:
        expected = _default_expected_evidence(trigger_type, target)
    if not observed:
        observed = [milestone_result.summary]

    return ReflectionRecord(
        trigger_type=trigger_type,
        slice_id=slice_id,
        milestone_id=milestone_result.milestone_id,
        target=target,
        expected_evidence=expected,
        observed_evidence=observed,
        changed_since_last_attempt=changed_since_last_attempt or [],
        failed_checks=[check.name for check in failed_checks],
        classification=classification,
        issue_kind=issue_kind,
        issue_subtype=issue_subtype,
        touched_files=_normalize_paths(touched_files),
        next_strategy=next_strategy,
        no_progress_count=no_progress_count,
        durable_memory_candidate=durable_memory_candidate,
        artifacts=milestone_result.artifacts,
    )


def build_work_package(
    *,
    slice_id: str,
    milestone_id: str,
    milestone_file: Path,
    classification: ReflectionClassification,
    trigger_type: str,
    failed_checks: list[str],
) -> WorkPackage:
    acceptance = [f"Milestone '{milestone_id}' passes with score 1.0"]
    acceptance.extend(f"check '{name}' passes" for name in failed_checks)
    if trigger_type == 'boot_failure':
        acceptance.insert(0, 'Target command boots and serves the milestone URL')

    return WorkPackage(
        slice_id=slice_id,
        goal=f"Make {milestone_id} pass on the next attempt",
        modify_files=list(DEFAULT_VERIFY_MODIFY_FILES),
        read_files=['src/agent_template', str(milestone_file)],
        acceptance_criteria=acceptance,
        evidence_required=['result.json', 'reflection.json', 'work-package.json'],
        non_goals=[
            'recursive agent execution',
            'autonomous retries',
            'milestone expansion beyond shell_boot',
        ],
        rollback_risk='Low: keep changes limited to the failing milestone path and its verifier contract.',
        escalation_conditions=[
            'The fix requires files outside the bounded modify_files set.',
            f"The expected behavior for {milestone_id} is incorrect in the milestone YAML or spec.",
            f"The repeated {classification} incident suggests a scope or spec issue rather than an implementation bug.",
        ],
    )
