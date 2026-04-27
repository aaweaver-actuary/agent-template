from pathlib import Path

from agent_template.ledger.state_store import StateStore
from agent_template.models import ReflectionRecord, RunState


def test_state_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)

    original = RunState(
        objective="test objective",
        repo_path="/tmp/repo",
        milestone_id="shell_boot",
        current_score=0.5,
        last_reflection=ReflectionRecord(
            trigger_type="failed_verifier",
            slice_id="slice-1",
            milestone_id="shell_boot",
            target="shell_boot",
            expected_evidence=["check taskbar should pass"],
            observed_evidence=["missing taskbar UI"],
            changed_since_last_attempt=["score did not improve from 0.5 to 0.5"],
            failed_checks=["taskbar"],
            classification="verification_failure",
            issue_kind="code",
            issue_subtype="missing_ui",
            touched_files=["src/agent_template/harness/desktop_shell/index.html"],
            next_strategy=["inspect taskbar markup"],
        ),
    )

    store.save(original)
    loaded = store.load()

    assert loaded.objective == original.objective
    assert loaded.repo_path == original.repo_path
    assert loaded.milestone_id == original.milestone_id
    assert loaded.current_score == original.current_score
    assert loaded.last_reflection is not None
    assert loaded.last_reflection.issue_subtype == "missing_ui"
    assert loaded.last_reflection.touched_files == [
        "src/agent_template/harness/desktop_shell/index.html"
    ]
