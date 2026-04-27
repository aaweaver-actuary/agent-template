from pathlib import Path

from agent_template.ledger.state_store import StateStore
from agent_template.models import RunState


def test_state_store_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)

    original = RunState(
        objective="test objective",
        repo_path="/tmp/repo",
        milestone_id="shell_boot",
        current_score=0.5,
    )

    store.save(original)
    loaded = store.load()

    assert loaded.objective == original.objective
    assert loaded.repo_path == original.repo_path
    assert loaded.milestone_id == original.milestone_id
    assert loaded.current_score == original.current_score
