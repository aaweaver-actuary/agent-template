import importlib
from pathlib import Path


def test_package_import_smoke() -> None:
    module = importlib.import_module("agent_template")

    assert callable(module.main)


def test_config_paths_are_path_safe(tmp_path: Path) -> None:
    config_module = importlib.import_module("agent_template.config")
    cfg = config_module.Config(
        paths=config_module.Paths(
            tmp=tmp_path / "tmp",
            state_file=tmp_path / "state.json",
            artifacts=tmp_path / "artifacts",
            logs=tmp_path / "logs",
            screenshots=tmp_path / "screenshots",
        )
    )

    assert cfg.screenshot_path("desktop") == tmp_path / "screenshots" / "desktop.png"
