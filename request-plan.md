# Request Plan

- request_id: shell_boot_run_once_mvp_2026_04_27
- user_goal: get the agent suite to the point where `agent-template run-once --milestone shell_boot` works end to end and matches the MVP behavior in `spec.md`
- current_request_state: request_review
- active_pr_scope: none
- completed_pr_scopes: [pr1_bootstrap_and_verify_contract, pr2_run_once_execution_and_artifacts, pr3_reflection_progress_and_work_package, pr4_verify_failure_reflection_regression]
- deferred_pr_scopes:
  - autonomous retry loops beyond single-run flow
  - recursive agent dispatch
  - long-term memory automation
  - milestone expansion beyond `shell_boot`
- blocked_pr_scopes: []
- ordered_pr_scopes:
  - id: pr1_bootstrap_and_verify_contract
    status: complete
    objective: remove import and packaging blockers, align the command surface with the spec, and make `shell_boot` verification load from milestone YAML
    completion_gates:
      - package import succeeds cleanly
      - CLI exposes a spec-aligned verify surface
      - shell_boot verification reads milestone YAML instead of hard-coded selectors
      - targeted bootstrap and verifier tests pass
  - id: pr2_run_once_execution_and_artifacts
    status: complete
    objective: implement the single-run controller that wires state, process management, verification, and artifact persistence together
    completion_gates:
      - `agent-template run-once --milestone shell_boot` executes end to end
      - state and core artifacts are written in a stable per-run layout
      - boot failures capture process output and skip browser checks
      - started services are cleaned up deterministically
  - id: pr3_reflection_progress_and_work_package
    status: complete
    objective: make failures actionable by adding richer reflection, stalled-progress detection, and bounded work-package output
    completion_gates:
      - failing runs emit structured reflection records
      - repeated no-improvement failures increment `no_progress_count`
      - stalled progress is classified explicitly
      - each failed run emits a bounded work-package artifact
  - id: pr4_verify_failure_reflection_regression
    status: complete
    objective: repair the verify failure-path contract so a failed verify run returns a clean failure result with reflection data instead of raising a TypeError
    completion_gates:
      - a failing verify invocation exits with failure status instead of raising TypeError
      - the verify failure path persists reflection data with the required `issue_kind` field
      - a focused CLI regression test fails on the pre-fix behavior and passes after the fix
      - targeted validation passes for the touched slice
- request_completion_gates:
  - the verifier for `shell_boot` is driven from milestone YAML rather than hard-coded selectors: complete
  - `agent-template run-once --milestone shell_boot` executes the run flow end to end against a controlled target or fixture harness: complete
  - the run flow writes state, result, screenshot, and process or log artifacts in a stable per-run layout: complete
  - a failing run produces a reflection record and a bounded next work package: complete
  - repeated no-improvement failures increment `no_progress_count` and classify stalled progress: complete
  - a passing rerun records a passing milestone result without manual state surgery: complete
- final_response_readiness: blocked_by_missing_github_identity_for_external_issue_sync
