from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from ..browser.playwright_runner import PlaywrightRunner
from ..models import CheckResult, MilestoneResult
from ..verifiers.browser_checks import (
    no_console_errors,
    no_network_failures,
    selector_exists,
)

DEFAULT_MILESTONE_PATH = Path(__file__).resolve().parents[1] / "milestones" / "desktop_shell.yaml"


class MilestoneTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["static_server"]
    url_path: str


class MilestoneCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: Literal["selector_exists"]
    selector: str
    required: bool = True

    @property
    def name(self) -> str:
        return self.id


class MilestoneWorkPackage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_modify_files: tuple[str, ...] = ()
    default_read_files: tuple[str, ...] = ()
    non_goals: tuple[str, ...] = ()


class MilestoneDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    target: MilestoneTarget
    checks: tuple[MilestoneCheck, ...]
    work_package: MilestoneWorkPackage | None = None

    @property
    def milestone_id(self) -> str:
        return self.id


class MilestoneManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    milestones: tuple[MilestoneDefinition, ...]


def _format_manifest_error(milestone_path: Path, error: ValidationError) -> ValueError:
    lines = [f"Invalid milestone manifest at {milestone_path}:"]
    for entry in error.errors():
        location = ".".join(str(part) for part in entry["loc"])
        message = entry["msg"]
        if "input" in entry:
            message = f"{message} (got {entry['input']!r})"
        lines.append(f"- {location}: {message}")
    return ValueError("\n".join(lines))


def load_milestone_definition(
    milestone_id: str,
    milestone_path: Path = DEFAULT_MILESTONE_PATH,
) -> MilestoneDefinition:
    try:
        raw_manifest = yaml.safe_load(milestone_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in milestone manifest {milestone_path}: {error}") from error

    try:
        manifest = MilestoneManifest.model_validate(raw_manifest)
    except ValidationError as error:
        raise _format_manifest_error(milestone_path, error) from error

    for milestone in manifest.milestones:
        if milestone.milestone_id == milestone_id:
            return milestone

    raise ValueError(f"Milestone {milestone_id!r} not found in {milestone_path}.")


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
        dom_snapshot = self.runner.dom_snapshot(milestone_id)

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
            artifacts=[screenshot, dom_snapshot],
        )

    def verify_shell_boot(self, url: str) -> MilestoneResult:
        return self.verify("shell_boot", url)
