from pathlib import Path

from agent_template.runtime.artifact_store import ArtifactStore


def test_write_text_creates_artifact(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact = store.write_text(
        run_id="run-1",
        kind="text",
        filename="note.txt",
        content="hello",
        label="note",
    )

    assert artifact.kind == "text"
    assert Path(artifact.path).exists()
    assert Path(artifact.path).read_text(encoding="utf-8") == "hello"
