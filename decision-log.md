# Decision Log

## 2026-04-27 - Phase 2 Rebaseline

### Decision 1: keep the runtime single-run

- Phase 2 preserves the Phase 1 execution model: verify -> reflect -> package next slice -> exit.
- Autonomous retry loops remain out of scope.

Reason:

- The current product boundary is a diagnostic and packaging loop, not an autonomous repair system.
- Deeper reflection and reusable packaging can be delivered without reopening retry policy.

### Decision 2: adopt `PyYAML` plus explicit schema validation

- Phase 2 replaces the hand-rolled YAML parsing path with `PyYAML`.
- Parsed manifests must validate into an explicit typed schema before use.

Reason:

- Manifest complexity is increasing to support reusable work-package metadata.
- The Phase 1 parser was acceptable as a proof of concept but is too fragile for the next contract expansion.

### Decision 3: make work-package bounds data-driven

- Work-package generation must derive file bounds from milestone and target metadata rather than a desktop-shell constant.
- Scope-delta classification is required when the likely fix falls outside those bounds.

Reason:

- The current hardcoded package path blocks reuse beyond the desktop harness.
- Phase 2 needs bounded but reusable slice generation across verifier targets.