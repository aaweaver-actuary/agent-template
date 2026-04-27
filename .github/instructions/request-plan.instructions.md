# Request Plan Policy

`request-plan.md` is the authoritative planning artifact for the active user request.

The request plan exists above any single PR scope. It tracks full-request intent, ordered PR scopes, scope status, and what still remains before the user request is complete.

## Rules

- Request Manager is the only role allowed to finalize request-level state transitions.
- The active request plan must describe only the current user request.
- A materially new user request must start from a fresh active request plan or an archived prior request plan.
- PR-scope completion must not be confused with request completion.
- The request plan must track ordered PR scopes and their status: planned, ready, in_progress, blocked, deferred, or complete.
- If there is any doubt whether a request is materially new, default to a fresh active request plan.

## Minimum Request Plan Contents

- request_id
- user_goal
- current_request_state
- ordered_pr_scopes
- active_pr_scope
- completed_pr_scopes
- deferred_pr_scopes
- blocked_pr_scopes
- request_completion_gates
- final_response_readiness

## Materially New Request Triggers

Start from a fresh active request plan when any of the following changes:

- the user reframes what done means
- the request objective changes materially
- the requested delivery shape changes materially
- the issue set changes enough that prior PR-scope planning no longer maps cleanly
- a previously complete request is reopened with materially different goals

## Required Request Manager Behavior

When a materially new request is detected, Request Manager must:

1. stop treating the prior active request plan as the source of truth for the new request
2. create or initialize a fresh active request plan for the new request, or explicitly archive the prior one
3. restate the new request scope, ordered PR scopes, and request-completion gates in the active request plan
4. continue orchestration only from the fresh active request plan

## Prohibited Behavior

- Do not continue using an old request plan that already implies `complete` when the new request changes completion semantics.
- Do not let a clean PR-scope result imply full-request completion unless the request plan says no unresolved PR scopes remain.
- Do not let administrative continuity override current request-level completion truth.

