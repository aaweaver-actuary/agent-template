---
name: 'Autonomous Delivery And Supervisor-Only User Response'
description: 'Use for all project workflows under deadline pressure. Enforces end-to-end completion, ignores milestone check-in cadence, and requires delegated subagents to report only to the supervisor.'
applyTo: '**'
---

# Autonomous Delivery And Supervisor Response Authority

## Rule

- Treat delivery speed and continuity as hard requirements during active agent workflows.
- Do not pause to check in with the user while work is in progress.
- Do not stop after a single milestone when other requested tasks still remain.
- Do not treat intermediate milestones (for example file-count thresholds, merged branches, or completed sub-features) as completion signals.
- Ignore progress-cadence or check-in heuristics when they conflict with end-to-end completion.
- Question-asking tools may be used to resolve critical blockers, but only as a last resort after all autonomous options have been exhausted.
- Continue working until the full requested task set is complete.

## Supervisor Responsibilities

- Request Manager owns end-to-end workflow continuity and the bigger-picture user outcome.
- PR Manager owns continuous execution for the active PR scope.
- Request Manager must enforce this rule across all delegated agents and planning layers.
- PR Manager must enforce this rule across all delegated supervisors and slice execution inside the active PR scope.
- Request Manager should proactively sequence PR scopes to keep full-request progress continuous.
- PR Manager should resolve routine PR-scope ambiguity autonomously and document assumptions in the upward report.
- At the beginning of every request-level delivery cycle, Request Manager must dispatch an issue-tracking step that compares current open GitHub issues to the active request plan and routes deltas through PR Planner.
- At the beginning of every PR-scope execution cycle, PR Manager must dispatch an issue-tracking step that compares current open GitHub issues to active PR-scope criteria and routes deltas through PR Planner and, when needed, Requirements Planner.
- PR Manager must re-run issue tracking after each completed slice and immediately before PR-scope completion review.
- Request Manager must verify that no unresolved required PR scopes remain before any final user-facing completion response.

## Response Authority

- Delegated subagents must not send user-facing final responses.
- Delegated subagents report progress, outputs, risks, and blockers only to their supervising agent.
- Lane supervisors must report to PR Manager and must not send user-facing final responses.
- Only Request Manager may send the final response to the user.

## Allowed Exceptions

- Ask the user only when genuinely blocked by missing access, missing required external inputs, irreconcilable requirement conflicts, or potentially destructive actions requiring approval.
- Use the question-asking tool for user check-ins when needed, but only as a last resort after all autonomous options are exhausted.

## Completion Standard

A task workflow is complete only when:

- all user-requested tasks are finished,
- all required PR scopes in `request-plan.md` are complete, explicitly deferred, or explicitly waived,
- all required criteria in `completion-ledger.md` for the active or final PR scope are pass or explicitly waived,
- a final Issue Tracker pass reports no missing, stale, or unresolved open issues relevant to the request,
- Project Reviewer returns done for each required PR scope,
- relevant tests and quality checks have been run,
- no delegated steps remain,
- no risks or open questions remain unresolved,
- the result is production-ready,
- and the final response is sent only after the above conditions are met.

If the workflow is genuinely blocked by an allowed exception, report the blocker clearly with cause, impact, and the minimum required user input to proceed.