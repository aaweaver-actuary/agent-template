# Completion Ledger Policy

`completion-ledger.md` is the authoritative live completion artifact for the active PR scope.

A materially new PR scope that changes completion semantics, delivery shape, issue membership, or PR strategy must start from a fresh active ledger state or an archived prior ledger. Previously completed scopes must not remain the active completion artifact when they would bias the current run.

## Rules

- PR Manager is the primary role allowed to finalize `completion-ledger.md` state transitions for the active PR scope.
- Project Manager may do the same only when it is acting as the legacy compatibility alias for PR Manager.
- The active ledger must describe only the current PR scope’s completion model.
- If a prior PR scope was completed under a different delivery contract, archive or replace that ledger state before continuing.
- Do not treat prior `complete` status as transferable when the new PR scope changes issue scope, acceptance semantics, bundling strategy, or PR strategy.
- A rebaselined PR scope must explicitly record that prior completion state is no longer the active source of truth.
- If there is any doubt whether the active PR scope is materially new, default to starting from a fresh active ledger state.

## Materially New PR Scope Triggers

Start from a fresh active ledger state when any of the following changes:

- bundled work becomes one-issue-per-PR work
- one-PR work becomes multi-PR work
- included issue set changes enough that prior completion evidence no longer maps cleanly
- PR-scope acceptance criteria change in a way that invalidates prior completion status
- the requested delivery artifact changes materially
- the active PR scope is redefined or explicitly rebaselined

## Required PR Manager Behavior

When a materially new PR scope is detected, PR Manager must:

1. stop treating the prior active ledger as the source of truth for completion of the new PR scope
2. create or initialize a fresh active ledger state for the new PR scope, or explicitly archive the prior one
3. restate the new PR-scope objective, issue membership, and completion gates in the active ledger
4. continue orchestration only from the fresh active ledger state

## Prohibited Behavior

- Do not continue using an old active ledger that already says `complete` when the new PR scope changes completion semantics.
- Do not infer that previously satisfied slices imply completion of the current PR scope unless they are explicitly revalidated against the new ledger.
- Do not let administrative continuity override current PR-scope completion truth.
