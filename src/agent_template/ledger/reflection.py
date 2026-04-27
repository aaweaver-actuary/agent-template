from __future__ import annotations

from pathlib import Path

from ..models import MilestoneResult, ReflectionRecord, WorkPackage


def build_reflection_record(
    *,
    trigger_type: str,
    slice_id: str,
    milestone_result: MilestoneResult,
    target: str,
    classification: str,
    issue_kind: str,
    changed_since_last_attempt: list[str] | None = None,
    no_progress_count: int = 0,
    next_strategy: list[str],
    durable_memory_candidate: bool = False,
) -> ReflectionRecord:
    failed_checks = [check for check in milestone_result.checks if not check.passed]

    expected = [f"check '{check.name}' should pass" for check in failed_checks]
    observed = [check.evidence or f"check '{check.name}' failed" for check in failed_checks]

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
    classification: str,
    trigger_type: str,
    failed_checks: list[str],
) -> WorkPackage:
    acceptance = [f"Milestone '{milestone_id}' passes with score 1.0"]
    acceptance.extend(f"check '{name}' passes" for name in failed_checks)
    if trigger_type == 'boot_failure':
        acceptance.insert(0, 'Target command boots and serves the milestone URL')

    return WorkPackage(
        slice_id=slice_id,
        goal=f'Make {milestone_id} pass on the next attempt',
        modify_files=['src/agent_template/harness/desktop_shell/index.html'],
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
            f'The expected behavior for {milestone_id} is incorrect in the milestone YAML or spec.',
            f'The repeated {classification} incident suggests a scope or spec issue rather than an implementation bug.',
        ],
    )
