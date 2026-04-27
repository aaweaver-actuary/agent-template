## 1. Define the target app context

A browser-based desktop shell with:
- wallpaper area
- taskbar
- start button / app launcher
- clock/status area
- desktop icons
- at least one launchable window
- close/minimize behavior

## 2. Make the verifier yaml-driven

load milestones/desktop_shell.yaml
for selected milestone:
  1. visit app URL
  2. evaluate each selector
  3. score checks
  4. screenshot page
  5. return MilestoneResult

## 3. Orchestration Loop

Note: we already have the data models for this -- we are missing the controller that wires them together.

- load RunState
- load next milestone
- start dev server
- run Playwright verifier
- save artifacts
- compare result to previous score
- if pass:
    - advance milestone
- if fail:
    - build ReflectionRecord
    - save reflection
    - update no_progress_count
    - produce next bounded work package
- save RunState

## 4. Make reflection more than “failed checks”

### The current reflection builder mostly says: 

- failed selector → 
    - expected check should pass → 
    - observed evidence 

### Add classification rules:

```
failed_verifier:
  UI element missing
  selector mismatch
  app did not boot
  runtime error
  network error
  test expectation stale

stalled_progress:
  same score as previous run
  same failed checks across attempts
  same files touched without criterion movement

scope_delta:
  needed file outside slice
  acceptance criterion wrong
  missing interface/spec
```

### Then the reflection record should answer:

```
What was expected?
What was observed?
What changed since last attempt?
Is this a code bug, test bug, spec bug, or scope problem?
What should the next attempt do differently?
Should this become durable memory?
```

## 5. Add progress/stall detection

This is what makes it “self-reflection” rather than “test failure logging.”

### Minimum algorithm:

```python
if result.score > previous_score:
    no_progress_count = 0
elif result.score == previous_score:
    no_progress_count += 1

if no_progress_count >= 2:
    trigger reflection with classification="stalled_progress"
```

### Later, make it richer by comparing

```
failed checks
files changed
test output
console errors
network failures
screenshot diffs
DOM snapshots
```

## 6. Generate the next work package

The runtime does not need to write code itself yet. The basic version can output a structured prompt/package for Copilot agents.

### Example output:

```Next slice: implement shell_boot milestone

Modify:
- src/App.tsx
- src/components/DesktopShell.tsx

Read:
- milestones/desktop_shell.yaml
- tests/e2e/desktop-shell.spec.ts

Acceptance criteria:
- [data-testid="desktop-root"] exists
- [data-testid="taskbar"] exists
- [data-testid="start-button"] exists
- verifier score = 1.0

Evidence required:
- npm test
- npm run dev + verifier
- screenshot artifact
```

## 7. Fix likely code-level blockers

Before the runtime will work cleanly:

* Change mutable dataclass defaults to field(default_factory=...).
* Convert config path strings to Path objects before using /.
* Avoid importing Playwright through package __init__.py.
* Fill empty sandbox.py, verifiers/base.py, and runtime entry points.
* Add CLI commands like:

```agent-template init
agent-template verify --milestone shell_boot --url http://localhost:3000
agent-template reflect --state .agent/state.json
agent-template run-once --milestone shell_boot
```

## 8. Define artifact schema

Specify what gets written per run:

```.agent/runs/{run_id}/
  state.json
  result.json
  reflection.md
  work-package.md
  screenshots/
  logs/
  dom-snapshot.html
```

## 9. Define milestone YAML format

Add a concrete schema:

```yaml
id: shell_boot
description: Basic desktop shell renders
url_path: /
checks:
  - id: desktop-root
    type: selector_exists
    selector: '[data-testid="desktop-root"]'
    required: true
  - id: start-button
    type: selector_exists
    selector: '[data-testid="start-button"]'
    required: true
passing_score: 1.0
```

## 10. Add failure-handling policy

Define what happens when the app cannot even boot:

```If dev server fails:
- capture stdout/stderr
- classify as runtime_error
- skip browser checks
- emit work package focused only on boot repair
```

## 11. Define “next bounded work package” contract

Make the generated package machine-readable enough for agents:

```yaml
slice_id: fix_shell_boot_start_button
goal: Make shell_boot pass
allowed_files:
  - src/App.tsx
  - src/components/DesktopShell.tsx
read_files:
  - milestones/desktop_shell.yaml
acceptance:
  - verifier shell_boot score == 1.0
non_goals:
  - styling polish
  - window manager behavior
evidence_required:
  - verifier result
  - screenshot

```

## Basic MVP sequence

Build it in this order:

1. Make the demo web app satisfy shell_boot.
2. Make the verifier read desktop_shell.yaml.
3. Add run-once: start app → verify → save artifacts/state.
4. Add reflection on failure.
5. Add no-progress detection.
6. Emit next-slice work packages.
7. Only then expand toward autonomous retry/replanning.

### Non-Goals

MVP does not:
- autonomously edit code
- recursively dispatch agents
- infer product requirements
- maintain long-term memory automatically
- attempt visual perfection
- implement a real OS/window manager

## Acceptance Criteria

MVP is functional when:
1. `agent-template run-once --milestone shell_boot` runs end-to-end.
2. It saves state, artifacts, verifier result, and screenshot.
3. It produces a ReflectionRecord on failure.
4. It increments no_progress_count on repeated failure.
5. It emits a bounded work package.
6. After fixing the app, the same command records a passing milestone.