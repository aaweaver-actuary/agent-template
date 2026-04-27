from pathlib import Path
from unittest.mock import Mock

from agent_template.models import ArtifactRef
from agent_template.verifiers.desktop_shell import DesktopShellVerifier


def _mock_locator(count: int):
    locator = Mock()
    locator.count.return_value = count
    return locator


def test_verify_shell_boot_loads_yaml_checks(tmp_path: Path) -> None:
    milestone_path = tmp_path / "desktop_shell.yaml"
    milestone_path.write_text(
        """
milestones:
  - id: shell_boot
    description: Shell boot checks
    checks:
      - name: desktop_root
        selector: \"[data-testid='desktop-root']\"
      - name: launch_button
        selector: \"[data-testid='launch-button']\"
""".strip(),
        encoding="utf-8",
    )

    page = Mock()
    page.locator.side_effect = [
        _mock_locator(1),
        _mock_locator(0),
    ]

    runner = Mock()
    runner.page = page
    runner.console_errors.return_value = []
    runner.network_failures.return_value = []
    runner.screenshot.return_value = ArtifactRef(
        kind="screenshot",
        path=".tmp/shell.png",
        label="shell_boot",
    )

    verifier = DesktopShellVerifier(runner, milestone_path=milestone_path)
    result = verifier.verify_shell_boot("http://localhost:3000")

    assert result.milestone_id == "shell_boot"
    assert result.passed is False
    assert result.score == 0.75
    assert [check.name for check in result.checks[:2]] == [
        "desktop_root",
        "launch_button",
    ]
    assert page.locator.call_args_list[0].args[0] == "[data-testid='desktop-root']"
    assert page.locator.call_args_list[1].args[0] == "[data-testid='launch-button']"
