# Agent Template

## Install

Create or refresh the local environment, then install the browser dependency:

```bash
uv sync
./.venv/bin/playwright install chromium
```

## Run Tests

Use the focused PR1 bundle when you are changing the manifest contract or verifier behavior:

```bash
./.venv/bin/pytest tests/test_cli.py tests/test_desktop_shell_verifier.py tests/test_run_once.py -q
```

## Run Once

Run the single verification pass against the checked-in `shell_boot` milestone:

```bash
./.venv/bin/agent-template run-once --milestone shell_boot
```

Use temporary output paths when you do not want to write into `.agent_template/`:

```bash
./.venv/bin/agent-template run-once --milestone shell_boot --state-path .tmp/manual/state.json --artifacts-path .tmp/manual/artifacts
```

## Artifact Layout

Each run writes a per-run directory under `.agent_template/artifacts/runs/<run_id>/` with:

- `state.json` for the saved run state
- `result.json` for the verifier result payload
- `reflection.json` when the run fails or stalls
- `work-package.json` when a reflection record is emitted
- `screenshot/` for browser screenshots
- `logs/` for target process stdout and stderr when boot commands are used

## Read reflection.json

`reflection.json` answers why the run failed or stalled. The most important fields are:

- `trigger_type` for what caused reflection to run
- `classification` for the broad failure class
- `issue_kind` for whether the problem looks like code, test, spec, or scope
- `failed_checks` for the stable verifier checks that failed
- `next_strategy` for the bounded next actions

## Read work-package.json

`work-package.json` is the machine-readable handoff for the next attempt. Check these fields first:

- `goal` for the next slice objective
- `modify_files` for the allowed write surface
- `read_files` for the required context
- `acceptance_criteria` for what must change
- `evidence_required` for the validation expected before closing the slice
- `escalation_conditions` for when the likely fix is outside the package bounds
