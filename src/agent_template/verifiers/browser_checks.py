from __future__ import annotations

from playwright.sync_api import Page

from ..models import CheckResult


def selector_exists(page: Page, name: str, selector: str) -> CheckResult:
    count = page.locator(selector).count()
    passed = count > 0
    evidence = f"selector={selector}, count={count}"
    return CheckResult(name=name, passed=passed, evidence=evidence)


def no_console_errors(console_errors: list[str]) -> CheckResult:
    passed = len(console_errors) == 0
    evidence = "no console errors" if passed else "\n".join(console_errors)
    return CheckResult(name="no_console_errors", passed=passed, evidence=evidence)


def no_network_failures(network_failures: list[str]) -> CheckResult:
    passed = len(network_failures) == 0
    evidence = "no network failures" if passed else "\n".join(network_failures)
    return CheckResult(name="no_network_failures", passed=passed, evidence=evidence)
