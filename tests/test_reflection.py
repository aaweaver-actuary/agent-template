from agent_template.ledger.reflection import build_reflection_record, classify_reflection_issue
from agent_template.models import CheckResult, MilestoneResult


def test_build_reflection_record_captures_failed_checks() -> None:
    result = MilestoneResult(
        milestone_id="shell_boot",
        passed=False,
        score=0.5,
        summary="test",
        checks=[
            CheckResult(name="desktop_root", passed=True, evidence="ok"),
            CheckResult(name="taskbar", passed=False, evidence="missing taskbar"),
        ],
    )

    reflection = build_reflection_record(
        trigger_type="failed_verifier",
        slice_id="slice-1",
        milestone_result=result,
        target="desktop shell boot",
        classification="verification_failure",
        issue_kind="code",
        issue_subtype="missing_ui",
        changed_since_last_attempt=["score dropped from 1.0 to 0.5"],
        touched_files=["src/agent_template/harness/desktop_shell/index.html"],
        no_progress_count=1,
        next_strategy=["inspect root layout"],
    )

    assert reflection.trigger_type == "failed_verifier"
    assert reflection.milestone_id == "shell_boot"
    assert reflection.classification == "verification_failure"
    assert reflection.issue_kind == "code"
    assert reflection.issue_subtype == "missing_ui"
    assert reflection.touched_files == ["src/agent_template/harness/desktop_shell/index.html"]
    assert reflection.changed_since_last_attempt == ["score dropped from 1.0 to 0.5"]
    assert reflection.no_progress_count == 1
    assert "missing taskbar" in reflection.observed_evidence


def test_classify_reflection_issue_distinguishes_verification_failure_kinds() -> None:
    code_issue = classify_reflection_issue(
        trigger_type="failed_verifier",
        failed_checks=["taskbar"],
        observed_evidence=["missing taskbar UI"],
        touched_files=["src/agent_template/harness/desktop_shell/index.html"],
        modify_files=["src/agent_template/harness/desktop_shell/index.html"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )
    test_issue = classify_reflection_issue(
        trigger_type="failed_verifier",
        failed_checks=["taskbar"],
        observed_evidence=["selector mismatch: taskbar exists but selector is stale"],
        touched_files=["tests/test_desktop_shell_verifier.py"],
        modify_files=["src/agent_template/harness/desktop_shell/index.html"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )
    spec_issue = classify_reflection_issue(
        trigger_type="failed_verifier",
        failed_checks=["taskbar"],
        observed_evidence=["acceptance criteria stale for shell layout"],
        touched_files=["spec.md"],
        modify_files=["src/agent_template/harness/desktop_shell/index.html"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )
    scope_issue = classify_reflection_issue(
        trigger_type="failed_verifier",
        failed_checks=["taskbar"],
        observed_evidence=["missing taskbar UI"],
        touched_files=["spec.md"],
        modify_files=["src/agent_template/harness/desktop_shell/index.html"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )

    assert code_issue.classification == "verification_failure"
    assert code_issue.issue_kind == "code"
    assert code_issue.issue_subtype == "missing_ui"

    assert test_issue.classification == "verification_failure"
    assert test_issue.issue_kind == "test"
    assert test_issue.issue_subtype == "selector_mismatch"

    assert spec_issue.classification == "verification_failure"
    assert spec_issue.issue_kind == "spec"
    assert spec_issue.issue_subtype == "stale_acceptance_criteria"

    assert scope_issue.classification == "scope_delta"
    assert scope_issue.issue_kind == "scope"
    assert scope_issue.issue_subtype == "outside_work_package"


def test_classify_reflection_issue_covers_boot_and_schema_failures() -> None:
    boot_issue = classify_reflection_issue(
        trigger_type="boot_failure",
        failed_checks=[],
        observed_evidence=["Traceback: runtime exploded before server boot"],
        touched_files=["src/agent_template/runtime/run_once.py"],
        modify_files=["src/agent_template/runtime/run_once.py"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )
    network_issue = classify_reflection_issue(
        trigger_type="boot_failure",
        failed_checks=[],
        observed_evidence=["network error: connection refused while starting target"],
        touched_files=["src/agent_template/runtime/run_once.py"],
        modify_files=["src/agent_template/runtime/run_once.py"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )
    schema_issue = classify_reflection_issue(
        trigger_type="schema_error",
        failed_checks=[],
        observed_evidence=["checks.0.type contains an unknown check type"],
        touched_files=["src/agent_template/milestones/desktop_shell.yaml"],
        modify_files=["src/agent_template/milestones/desktop_shell.yaml"],
        previous_failed_checks=[],
        previous_touched_files=[],
    )

    assert boot_issue.classification == "boot_failure"
    assert boot_issue.issue_kind == "code"
    assert boot_issue.issue_subtype == "runtime_error"

    assert network_issue.classification == "boot_failure"
    assert network_issue.issue_kind == "code"
    assert network_issue.issue_subtype == "network_error"

    assert schema_issue.classification == "schema_error"
    assert schema_issue.issue_kind == "spec"
    assert schema_issue.issue_subtype == "schema_violation"
