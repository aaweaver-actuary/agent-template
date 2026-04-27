from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..browser.playwright_runner import PlaywrightRunner
from ..models import CheckResult, MilestoneResult
from ..verifiers.browser_checks import (
    no_console_errors,
    no_network_failures,
    selector_exists,
)

DEFAULT_MILESTONE_PATH = Path(__file__).resolve().parents[1] / "milestones" / "desktop_shell.yaml"


@dataclass(frozen=True)
class MilestoneCheck:
    name: str
    selector: str


@dataclass(frozen=True)
class MilestoneDefinition:
    milestone_id: str
    description: str
    checks: tuple[MilestoneCheck, ...]


def _parse_scalar(line: str) -> str:
    _, value = line.split(":", 1)
    value = value.strip()
    if value[:1] in {"'", '"'} and value[-1:] == value[:1]:
        return value[1:-1]
    return value


def load_milestone_definition(
    milestone_id: str,
    milestone_path: Path = DEFAULT_MILESTONE_PATH,
) -> MilestoneDefinition:
    current_id: str | None = None
    current_description = ""
    current_checks: list[MilestoneCheck] = []
    current_check_name: str | None = None
    current_check_selector: str | None = None

    def finalize_check() -> None:
        nonlocal current_check_name, current_check_selector
        if current_check_name is None:
            return
        if current_check_selector is None:
            raise ValueError(f"Missing selector for milestone check '{current_check_name}'.")
        current_checks.append(
            MilestoneCheck(name=current_check_name, selector=current_check_selector)
        )
        current_check_name = None
        current_check_selector = None

    def finalize_milestone() -> MilestoneDefinition | None:
        finalize_check()
        if current_id != milestone_id:
            return None
        return MilestoneDefinition(
            milestone_id=current_id,
            description=current_description,
            checks=tuple(current_checks),
        )

    for raw_line in milestone_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if not stripped:
            continue

        if indent == 2 and stripped.startswith("- id:"):
            found = finalize_milestone()
            if found is not None:
                return found
            current_id = _parse_scalar(stripped)
            current_description = ""
            current_checks = []
            current_check_name = None
            current_check_selector = None
            continue

        if current_id != milestone_id:
            continue

        if indent == 4 and stripped.startswith("description:"):
            current_description = _parse_scalar(stripped)
            continue

        if indent == 6 and stripped.startswith("- name:"):
            finalize_check()
            current_check_name = _parse_scalar(stripped)
            continue

        if indent == 8 and stripped.startswith("selector:"):
            current_check_selector = _parse_scalar(stripped)

    found = finalize_milestone()
    if found is not None:
        return found

    raise ValueError(f"Milestone '{milestone_id}' not found in {milestone_path}.")


class DesktopShellVerifier:
    """Version 1 verifier for a desktop-like shell app."""

    def __init__(
        self,
        runner: PlaywrightRunner,
        milestone_path: Path = DEFAULT_MILESTONE_PATH,
    ) -> None:
        self.runner = runner
        self.milestone_path = milestone_path

    def verify(self, milestone_id: str, url: str) -> MilestoneResult:
        milestone = load_milestone_definition(milestone_id, self.milestone_path)
        self.runner.goto(url)
        screenshot = self.runner.screenshot(milestone_id)

        checks: list[CheckResult] = [
            selector_exists(self.runner.page, check.name, check.selector)
            for check in milestone.checks
        ]
        checks.extend(
            [
                no_console_errors(self.runner.console_errors()),
                no_network_failures(self.runner.network_failures()),
            ]
        )

        passed_count = sum(1 for check in checks if check.passed)
        score = passed_count / len(checks)
        passed = all(check.passed for check in checks)

        return MilestoneResult(
            milestone_id=milestone_id,
            passed=passed,
            score=score,
            checks=checks,
            summary=milestone.description,
            artifacts=[screenshot],
        )

    def verify_shell_boot(self, url: str) -> MilestoneResult:
        return self.verify("shell_boot", url)
