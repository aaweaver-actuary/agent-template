from pathlib import Path
from unittest.mock import Mock

from agent_template.models import ArtifactRef
from agent_template.verifiers.desktop_shell import (
    DesktopShellVerifier,
    load_milestone_definition,
)


def _mock_locator(count: int):
    locator = Mock()
    locator.count.return_value = count
    return locator


def test_verify_shell_boot_loads_yaml_checks(tmp_path: Path) -> None:
    milestone_path = tmp_path / "desktop_shell.yaml"
    milestone_path.write_text(
        """
version: 1
milestones:
  - id: shell_boot
    description: Shell boot checks
    target:
      kind: static_server
      url_path: /
    checks:
      - id: desktop_root
        type: selector_exists
        selector: "[data-testid='desktop-root']"
      - id: launch_button
        type: selector_exists
        selector: "[data-testid='launch-button']"
    work_package:
      default_modify_files:
        - src/agent_template/harness/desktop_shell/index.html
      default_read_files:
        - src/agent_template/milestones/desktop_shell.yaml
      non_goals:
        - no autonomous retries
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
    runner.dom_snapshot.return_value = ArtifactRef(
        kind="dom_snapshot",
        path=".tmp/shell.html",
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
    assert [artifact.kind for artifact in result.artifacts] == [
        "screenshot",
        "dom_snapshot",
    ]
    runner.goto.assert_called_once_with("http://localhost:3000")
    runner.dom_snapshot.assert_called_once_with("shell_boot")
    assert page.locator.call_args_list[0].args[0] == "[data-testid='desktop-root']"
    assert page.locator.call_args_list[1].args[0] == "[data-testid='launch-button']"


def test_load_milestone_definition_exposes_work_package_metadata(tmp_path: Path) -> None:
    milestone_path = tmp_path / "desktop_shell.yaml"
    milestone_path.write_text(
        """
version: 1
milestones:
  - id: shell_boot
    description: Shell boot checks
    target:
      kind: static_server
      url_path: /
    checks:
      - id: desktop_root
        type: selector_exists
        selector: "[data-testid='desktop-root']"
    work_package:
      default_modify_files:
        - src/agent_template/harness/desktop_shell/index.html
      default_read_files:
        - src/agent_template/milestones/desktop_shell.yaml
      non_goals:
        - milestone expansion beyond shell_boot
""".strip(),
        encoding="utf-8",
    )

    milestone = load_milestone_definition("shell_boot", milestone_path)

    assert milestone.milestone_id == "shell_boot"
    assert milestone.target.kind == "static_server"
    assert milestone.target.url_path == "/"
    assert milestone.checks[0].name == "desktop_root"
    assert milestone.work_package is not None
    assert milestone.work_package.default_modify_files == (
        "src/agent_template/harness/desktop_shell/index.html",
    )
    assert milestone.work_package.default_read_files == (
        "src/agent_template/milestones/desktop_shell.yaml",
    )
    assert milestone.work_package.non_goals == (
        "milestone expansion beyond shell_boot",
    )


def test_load_milestone_definition_rejects_unknown_check_type_with_actionable_error(
    tmp_path: Path,
) -> None:
    milestone_path = tmp_path / "desktop_shell.yaml"
    milestone_path.write_text(
        """
version: 1
milestones:
  - id: shell_boot
    description: Shell boot checks
    target:
      kind: static_server
      url_path: /
    checks:
      - id: desktop_root
        type: unexpected_check
        selector: "[data-testid='desktop-root']"
""".strip(),
        encoding="utf-8",
    )

    try:
        load_milestone_definition("shell_boot", milestone_path)
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected schema validation failure")

    assert "unexpected_check" in message
    assert "selector_exists" in message
    assert "checks.0.type" in message


def test_load_milestone_definition_requires_manifest_version(tmp_path: Path) -> None:
    milestone_path = tmp_path / "desktop_shell.yaml"
    milestone_path.write_text(
        """
milestones:
  - id: shell_boot
    description: Shell boot checks
    target:
      kind: static_server
      url_path: /
    checks:
      - id: desktop_root
        type: selector_exists
        selector: "[data-testid='desktop-root']"
""".strip(),
        encoding="utf-8",
    )

    try:
        load_milestone_definition("shell_boot", milestone_path)
    except ValueError as error:
        message = str(error)
    else:
        raise AssertionError("expected schema validation failure")

    assert "version" in message
    assert str(milestone_path) in message
