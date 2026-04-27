from agent_template.ledger.reflection import build_reflection_record
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
        classification="implementation_bug",
        issue_kind="code",
        changed_since_last_attempt=["score dropped from 1.0 to 0.5"],
        no_progress_count=1,
        next_strategy=["inspect root layout"],
    )

    assert reflection.trigger_type == "failed_verifier"
    assert reflection.milestone_id == "shell_boot"
    assert reflection.issue_kind == "code"
    assert reflection.changed_since_last_attempt == ["score dropped from 1.0 to 0.5"]
    assert reflection.no_progress_count == 1
    assert "missing taskbar" in reflection.observed_evidence
