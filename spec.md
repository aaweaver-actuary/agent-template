# Phase 2 / MVP 2 Specification

## Scope Reset

This specification supersedes the Phase 1 MVP spec as the active product definition for the next delivery cycle.

Phase 1 is complete and remains the baseline:

- `agent-template run-once --milestone shell_boot` works end to end.
- The verifier reads milestone checks from YAML.
- Runs persist state, result, screenshot, reflection, and work-package artifacts.
- The runtime is intentionally single-run: verify -> reflect -> package next slice.

Phase 2 builds on that baseline. It does not reopen Phase 1 acceptance criteria unless a change below explicitly does so.

## Product Goal

Make the single-run verifier loop more reusable and more diagnostically useful without introducing autonomous retry behavior.

At the end of Phase 2, an operator should be able to:

- install and run the project from the README alone,
- execute a single verification run with predictable artifacts,
- understand whether a failure is caused by code, test selectors, stale spec expectations, or package-boundary scope,
- see a DOM snapshot alongside the screenshot,
- and hand the emitted work package to a downstream agent without desktop-shell-specific hardcoding.

## Goals

1. Replace the fragile hand-rolled YAML parsing path with a supported parsing and validation boundary.
2. Make milestone and work-package contracts reusable beyond the desktop harness.
3. Improve reflection quality so failures are classified into actionable code, test, spec, or scope categories.
4. Add DOM snapshot capture to the run artifacts.
5. Detect repeated-touch/no-movement incidents using file changes and failure signatures, not score alone.
6. Add a short operator README that explains installation, tests, `run-once`, artifact layout, and how to read `reflection.json` and `work-package.json`.
7. Preserve the Phase 1 execution model: one run performs verify -> reflect -> package next slice, then exits.

## Explicit Non-Goals

- No autonomous retry loop inside `run-once`.
- No recursive agent dispatch.
- No autonomous code editing.
- No multi-run planner beyond persisting state needed for the next single run.
- No visual diffing requirement.
- No milestone expansion that depends on a richer application than the current harness and verifier can support.
- No attempt to turn the demo harness into a full desktop or window-manager product.

## Architectural Decisions

### 1. YAML Loading Boundary

Phase 2 adopts `PyYAML` for YAML parsing.

Requirements:

- YAML is parsed with `PyYAML` rather than a hand-rolled parser.
- Parsed data is validated against an explicit typed schema before use.
- Invalid milestone files fail with actionable schema errors.
- Silent fallback behavior is forbidden.

Rationale:

- Phase 1 proved the manifest-driven flow.
- Phase 2 needs a stable parsing boundary before the manifest grows to support reusable work-package metadata.

### 2. Keep the Runtime Single-Run

Phase 2 keeps the runtime as a single-run controller.

Required control flow:

1. load previous state,
2. boot target if needed,
3. verify milestone,
4. persist artifacts,
5. reflect on failure or stall,
6. emit the next bounded work package,
7. save updated state,
8. exit.

Autonomous retries remain out of scope unless a later spec explicitly reopens that decision.

### 3. Make Work Packages Data-Driven

The next-slice package must stop hardcoding the desktop harness path.

Requirements:

- Work-package generation must derive allowed files and context from milestone metadata plus incident context.
- The generator may still provide defaults, but those defaults must come from the milestone definition or verifier target type, not from a fixed desktop-shell implementation path.
- A scope delta must be raised when the likely fix requires files outside the bounded modify set.

## Interface Contracts

### Milestone Manifest Contract

Phase 2 milestone files must validate into an explicit schema. The exact model names are implementation-defined, but the contract must support the following structure:

```yaml
version: 1
milestones:
  - id: shell_boot
    description: App boots into a recognizable desktop shell
    target:
      kind: static_server
      url_path: /
    checks:
      - id: desktop_root
        type: selector_exists
        selector: "[data-testid='desktop-root']"
        required: true
      - id: start_button
        type: selector_exists
        selector: "[data-testid='start-button']"
        required: true
    work_package:
      default_modify_files:
        - src/agent_template/harness/desktop_shell/index.html
      default_read_files:
        - src/agent_template/milestones/desktop_shell.yaml
      non_goals:
        - autonomous retries
        - milestone expansion beyond shell_boot
```

Required manifest behavior:

- `version` is mandatory.
- Each milestone has a stable `id` and `description`.
- Each check has a stable `id`, a `type`, and type-specific fields.
- Work-package hints are optional per milestone, but when present they are authoritative defaults for package generation.
- Unknown or malformed check types fail validation.

### Reflection Contract

Phase 2 reflection must keep broad and narrow cause information separate.

Required fields:

- `trigger_type`: why reflection was produced.
- `classification`: one of `verification_failure`, `stalled_progress`, `scope_delta`, `boot_failure`, or `schema_error`.
- `issue_kind`: one of `code`, `test`, `spec`, or `scope`.
- `issue_subtype`: a narrower reason.
- `changed_since_last_attempt`: human-readable deltas.
- `failed_checks`: stable failing check identifiers.
- `touched_files`: files changed since the previous run when available.
- `next_strategy`: concrete next actions.

Minimum required `issue_subtype` coverage:

- `selector_mismatch`
- `missing_ui`
- `runtime_error`
- `network_error`
- `stale_acceptance_criteria`
- `outside_work_package`
- `schema_violation`
- `same_files_same_failure`

Classification rules must support at least these distinctions:

- missing selector because the UI is absent -> `issue_kind=code`, `issue_subtype=missing_ui`
- missing selector because the selector is wrong but the UI exists -> `issue_kind=test`, `issue_subtype=selector_mismatch`
- current product behavior conflicts with stale acceptance criteria -> `issue_kind=spec`, `issue_subtype=stale_acceptance_criteria`
- likely fix requires files outside the bounded modify set -> `issue_kind=scope`, `issue_subtype=outside_work_package`

### Repeated-Touch Detection Contract

Phase 2 must improve stall detection beyond score comparison.

Requirements:

- The runtime compares the current failed-check signature to the previous failed-check signature.
- The runtime compares the current touched-file set to the previous touched-file set when that data is available.
- If the failure signature is unchanged and the touched files substantially overlap without criterion movement, the incident is classified as `stalled_progress` with `issue_subtype=same_files_same_failure` unless stronger evidence points to `scope_delta`.
- If file-change data is unavailable, the runtime must degrade gracefully and record that limitation in `changed_since_last_attempt`.

`criterion movement` means at least one of:

- score improvement,
- a changed failed-check set,
- a changed issue classification,
- or a resolved acceptance mismatch.

### Work-Package Contract

Phase 2 work packages remain machine-readable and bounded.

Required fields:

- `slice_id`
- `goal`
- `modify_files`
- `read_files`
- `acceptance_criteria`
- `evidence_required`
- `non_goals`
- `rollback_risk`
- `escalation_conditions`

Required behavior:

- `modify_files` must be derived from milestone metadata, verifier target metadata, or explicit incident escalation, not from a desktop-shell constant.
- `escalation_conditions` must explicitly include the case where the likely fix requires files outside the bounded package.
- Work packages generated from a stale selector or stale acceptance criteria must tell the downstream agent to inspect test/spec surfaces rather than product code first.

### Artifact Contract

Each run continues to write a stable per-run directory. Phase 2 extends that contract with a DOM snapshot artifact and clearer operator-facing semantics.

Required run layout:

```
.agent_template/
  state.json
  artifacts/
    runs/{run_id}/
      state.json
      result.json
      reflection.json        # present for failed, stalled, or schema-error runs
      work-package.json      # present whenever reflection is emitted
      screenshots/
      dom/
        dom-snapshot.html    # present when browser verification reached page load
      stdout/
      stderr/
```

Requirements:

- screenshot capture remains required for browser-verification runs,
- DOM snapshot capture is required whenever the verifier can reach the page,
- boot failures may omit screenshot and DOM snapshot, but must include process artifacts when available,
- artifact references in result and reflection payloads must point to the persisted files.

### Operator Documentation Contract

`README.md` must stop being empty.

Phase 2 requires a short operator document with the following sections:

- install the project,
- run the test suite,
- run `agent-template run-once --milestone shell_boot`,
- artifact layout overview,
- how to interpret `reflection.json`,
- how to interpret `work-package.json`.

This is operator documentation, not a contributor handbook. Keep it short and executable.

## Acceptance Criteria

Phase 2 is complete only when all of the following are true:

1. The active spec and implementation continue to support a single-run `agent-template run-once --milestone shell_boot` flow with no autonomous retry loop.
2. Milestone YAML loading uses `PyYAML` and explicit schema validation, and malformed manifests fail with actionable validation errors.
3. A verifier run that reaches the page persists both a screenshot artifact and a DOM snapshot artifact.
4. Reflection artifacts distinguish broad cause and narrow subtype, and can differentiate code, test, spec, and scope failures for the required cases in this spec.
5. Repeated-touch detection uses file changes plus failed-check signatures when available, not score alone.
6. A scope delta is emitted when the likely fix requires files outside the bounded work package.
7. Work-package generation is reusable and no longer hardcoded to the desktop harness path.
8. `README.md` explains install, tests, `run-once`, artifact layout, `reflection.json`, and `work-package.json`.
9. Focused validation covers the new parser boundary, DOM snapshot persistence, reflection classification, repeated-touch detection, reusable work-package generation, and README command paths.

## Recommended Implementation Order

1. Rebaseline the planning artifacts for Phase 2, then replace the README placeholder with the required operator doc so the command surface and artifact expectations are explicit.
2. Introduce the typed milestone manifest contract and switch parsing to `PyYAML` with explicit validation errors.
3. Extend verifier artifact capture to persist DOM snapshots and expose them through the existing artifact references.
4. Expand reflection data and classification logic to support `issue_kind`, `issue_subtype`, stale-criteria detection, selector mismatch vs missing UI, and scope-delta detection.
5. Add repeated-touch detection using failed-check signatures plus touched-file comparison with graceful degradation when file data is unavailable.
6. Refactor work-package generation so milestone metadata drives file bounds and escalation rules instead of desktop-shell hardcoding.
7. Add or update focused tests for the parser contract, artifact persistence, reflection taxonomy, repeated-touch detection, and work-package generation.

## Notes For Request-Level Replanning

This is a materially new request relative to the completed Phase 1 MVP. The active request plan and completion ledger should be rebaselined by their owning roles before implementation proceeds, because prior completion evidence is no longer the active request truth for Phase 2.