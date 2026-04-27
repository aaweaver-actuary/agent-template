# Project Agent Execution Rules

## Autonomous Completion

- Treat delivery speed and continuity as hard requirements during active workflows.
- Do not pause for user check-ins while work is in progress.
- Do not treat intermediate milestones (for example file-count thresholds, merged branches, or completed sub-features) as completion signals.
- Ignore progress-cadence or check-in heuristics when they conflict with end-to-end completion.
- Continue working until the full requested task set is complete and production-ready.

## Response Authority

- Delegated subagents must not send user-facing final responses.
- Delegated subagents report progress, outputs, risks, and blockers only to their supervising agent.
- Lane supervisors report to the Project Manager and must not send user-facing final responses.
- Only the Project Manager may send the final response to the user.

## Artifact Ownership

- Project Manager owns `completion-ledger.md` and is the only role that may finalize request state transitions.
- Requirements Planner owns `spec.md` and `decision-log.md`.
- Work Planner owns bounded slice-package definitions.
- Implementer owns code and tests for one slice.
- Reviewer owns slice verdicts against explicit criteria.
- Issue Tracker owns structured issue delta reports.
- Memory Researcher owns `.memories/*` updates.

## Delivery Loop

1. Project Manager defines or refreshes request state in `completion-ledger.md`.
2. Issue Tracker runs and emits structured external issue deltas.
3. Requirements Planner updates `spec.md` and `decision-log.md` and proposes ledger updates.
4. Work Planner emits one bounded slice package.
5. Project Manager routes that package to Frontend Supervisor, Backend Supervisor, or Full-Stack Supervisor.
6. Lane supervisor coordinates exactly one slice through Implementer.
7. Reviewer validates when required by slice risk conditions.
8. Project Manager updates `completion-ledger.md` with slice evidence and uncovered criteria.
9. Issue Tracker runs again at cycle boundary.
10. Project Reviewer evaluates done-or-not-done from ledger evidence.
11. Project Manager marks complete only when all completion gates are satisfied.

## Completion Gate

A workflow is complete only when all requested tasks are finished, all required criteria in `completion-ledger.md` are pass or explicitly waived, a final Issue Tracker pass reports clean status, Project Reviewer returns done, relevant checks are run, no delegated steps remain, and no unresolved risks or open questions remain.

If genuinely blocked by missing access, missing required external input, irreconcilable requirement conflicts, or potentially destructive actions requiring approval, report the blocker with cause, impact, and the minimum required user input to proceed.

## Repository Memory Culture

- Start each workflow by ensuring `.memories/` exists at the repository root and that `.memories/00index.md` and `.memories/00template.md` are present.
- Treat `.memories/` as the single source of truth for repository memory.
- Treat `completion-ledger.md` as the single source of truth for active request completion state.
- Do not use `/memories/repo/` or other non-repository memory namespaces as authoritative sources for repository facts.
- If duplicate memory exists outside `.memories/`, re-verify and migrate it into `.memories/`, then remove or deprecate the duplicate copy.
- Route repository-memory lookup questions through Memory Finder and repository-memory writes or updates through Memory Researcher.
- When you discover durable repository facts, workflow quirks, or useful commands, surface them as memory candidates so Memory Researcher can verify and record them.

## Issue To Plan Synchronization

- At the start of every Project Manager delivery cycle, dispatch Issue Tracker to collect external issue deltas.
- Route issue deltas through Requirements Planner before any additional implementation proceeds.

## GitHub Issues As Live Requirements Channel

- Treat open GitHub issues as the primary in-flight communication channel for new or changed requirements while the agent team is working.
- Project Manager must re-dispatch Issue Tracker after each completed slice, before choosing the next work item, and immediately before the final response.
- If an issue introduces or changes requirements, integrate that change into `spec.md` and request criteria before more implementation proceeds.
- Final user response is forbidden until the final Issue Tracker pass is clean.
- Lane supervisors must return control after each bounded slice so Project Manager can absorb new issue-driven requirements.

## Bounded Handoff Contract

Every execution handoff must include:

- objective
- exact files allowed to modify
- exact files allowed to read
- acceptance criteria for the slice
- required tests or commands
- known dependencies
- explicit non-goals
- rollback risk
- escalation conditions
- explicit instruction not to inspect beyond package unless blocked

## Escalation And Retry Rules

- Escalation chain: Implementer -> Lane Supervisor -> Work Planner -> Requirements Planner -> Project Manager.
- Retry budget: each slice may be retried at most 2 times locally.
- After 1 failed retry: lane-supervisor review is required.
- After 2 failed retries: escalation to Work Planner is mandatory; no third local retry.
- Scope Delta Rule: escalate `scope_delta` when required work exceeds package boundaries or criteria assumptions.

## Supervisor Lane Routing

- Project Manager is the user-facing orchestration entrypoint and the only role authorized to send final user responses.
- For implementation delivery, Project Manager must dispatch Frontend Supervisor, Backend Supervisor, or Full-Stack Supervisor based on feature scope.
- Re-evaluate lane assignment at each cycle boundary before selecting the next implementation work item.
