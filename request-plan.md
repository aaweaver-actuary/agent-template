# Request Plan

- request_id: phase2_single_run_diagnostics_2026_04_27
- user_goal: update the Phase 2 spec baseline and complete Phase 2 while preserving the single-run verify -> reflect -> package flow with no autonomous retry loop
- current_request_state: pr_scope_in_progress
- request_level_issue_status: clean
- active_pr_scope: pr3_phase2_reflection_taxonomy_and_repeated_touch_detection
- completed_pr_scopes: [pr1_phase2_manifest_contract_and_operator_readme, pr2_phase2_dom_snapshot_and_artifact_contract]
- deferred_pr_scopes:
  - autonomous retry loops
  - recursive agent dispatch
  - autonomous code editing
  - milestone expansion beyond `shell_boot`
- blocked_pr_scopes: []
- ordered_pr_scopes:
  - id: pr1_phase2_manifest_contract_and_operator_readme
    status: complete
    objective: establish the Phase 2 interface boundary by replacing the hand-rolled milestone parser with a typed `PyYAML` manifest contract and by shipping the required operator README
    completion_gates:
      - `README.md` explains install, tests, `run-once`, artifact layout, `reflection.json`, and `work-package.json`
      - milestone loading uses `PyYAML`
      - malformed manifests fail with actionable validation errors
      - the verifier still loads `shell_boot` from milestone data
      - focused parser and verifier tests pass
  - id: pr2_phase2_dom_snapshot_and_artifact_contract
    status: complete
    objective: extend the per-run artifact contract so a page-reaching verification persists a DOM snapshot alongside the screenshot without changing the single-run controller shape
    completion_gates:
      - a verification run that reaches the page writes both screenshot and DOM snapshot artifacts
      - result and reflection artifact references point to persisted files
      - boot failures may omit page artifacts but still persist process artifacts
      - focused artifact tests pass
  - id: pr3_phase2_reflection_taxonomy_and_repeated_touch_detection
    status: in_progress
    objective: make reflection diagnostically useful by separating broad classification from narrow subtype and by detecting same-files same-failure incidents without introducing retries
    completion_gates:
      - reflection artifacts distinguish `issue_kind` and `issue_subtype`
      - required subtype coverage is implemented
      - repeated-touch detection uses failed checks plus touched files when available and degrades gracefully when not
      - focused reflection and run-once tests pass
  - id: pr4_phase2_data_driven_work_package_and_scope_delta
    status: planned
    objective: make next-slice packaging reusable by deriving bounds from manifest and target metadata, and emit `scope_delta` when the likely fix is outside the bounded package
    completion_gates:
      - work packages no longer hardcode the desktop-shell implementation path
      - package bounds come from manifest or target metadata plus incident context
      - stale selector and stale acceptance incidents direct downstream work to test or spec surfaces first
      - out-of-bounds fixes emit `scope_delta`
      - focused work-package and end-to-end validation passes
- request_completion_gates:
  - preserve single-run `run-once`
  - switch milestone loading to `PyYAML` plus explicit schema validation
  - persist screenshot plus DOM snapshot when page load is reached
  - expand reflection to broad and narrow failure taxonomy
  - use failed-check signatures plus touched files for repeated-touch detection
  - emit `scope_delta` when likely fixes exceed bounds
  - generate work packages from manifest or target metadata instead of desktop-shell constants
  - ship the short operator README
  - cover the new parser, artifact, reflection, repeated-touch, packaging, and README command paths with focused validation
- final_response_readiness: not_ready
