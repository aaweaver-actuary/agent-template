from pathlib import Path
import tomllib

import agent_template.cli as cli
from agent_template.models import CheckResult, MilestoneResult


def test_console_script_matches_package_name() -> None:
    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
    )

    assert pyproject["project"]["scripts"] == {
        "agent-template": "agent_template:main"
    }


def test_verify_cli_dispatches_to_verify_handler(monkeypatch) -> None:
    called = {}

    def fake_run_verify(args) -> int:
        called["milestone"] = args.milestone
        called["url"] = args.url
        return 0

    monkeypatch.setattr(cli, "run_verify", fake_run_verify)

    exit_code = cli.main(
        ["verify", "--milestone", "shell_boot", "--url", "http://localhost:3000"]
    )

    assert exit_code == 0
    assert called == {
        "milestone": "shell_boot",
        "url": "http://localhost:3000",
    }


def test_run_once_cli_dispatches_to_run_once_handler(monkeypatch) -> None:
    called = {}

    def fake_run_once(args) -> int:
        called["milestone"] = args.milestone
        called["url"] = args.url
        return 0

    monkeypatch.setattr(cli, "run_run_once", fake_run_once)

    exit_code = cli.main(["run-once", "--milestone", "shell_boot"])

    assert exit_code == 0
    assert called == {
        "milestone": "shell_boot",
        "url": None,
    }


def test_verify_cli_returns_failure_and_persists_reflection_on_failed_verify(
    monkeypatch, tmp_path
) -> None:
    captured = {}

    class FakeRunner:
        def __init__(self, store, run_id) -> None:
            self.store = store
            self.run_id = run_id

        def start(self, *, headless: bool) -> None:
            captured["headless"] = headless

        def close(self) -> None:
            captured["closed"] = True

    class FakeVerifier:
        def __init__(self, runner, milestone_path) -> None:
            captured["milestone_path"] = str(milestone_path)

        def verify(self, milestone: str, url: str) -> MilestoneResult:
            captured["verify_call"] = {"milestone": milestone, "url": url}
            return MilestoneResult(
                milestone_id=milestone,
                passed=False,
                score=0.5,
                summary="taskbar missing",
                checks=[
                    CheckResult(
                        name="taskbar",
                        passed=False,
                        evidence="taskbar missing",
                    )
                ],
            )

    class FakeStateStore:
        def __init__(self, path) -> None:
            captured["state_path"] = str(path)

        def save(self, state) -> None:
            captured["state"] = state

    monkeypatch.setattr(
        "agent_template.browser.playwright_runner.PlaywrightRunner", FakeRunner
    )
    monkeypatch.setattr(
        "agent_template.verifiers.desktop_shell.DesktopShellVerifier", FakeVerifier
    )
    monkeypatch.setattr(
        "agent_template.ledger.state_store.StateStore", FakeStateStore
    )

    exit_code = cli.main(
        [
            "verify",
            "--milestone",
            "shell_boot",
            "--url",
            "http://localhost:3000",
            "--state-path",
            str(tmp_path / "state.json"),
            "--artifacts-path",
            str(tmp_path / "artifacts"),
        ]
    )

    assert exit_code == 1
    assert captured["verify_call"] == {
        "milestone": "shell_boot",
        "url": "http://localhost:3000",
    }
    assert captured["closed"] is True
    assert captured["state"].last_reflection is not None
    assert captured["state"].last_reflection.issue_kind == "code"
