---
name: 'Reflection Trigger Policy'
description: 'Use when coordinating slices, handling retries, diagnosing blocked work, or reconciling verifier evidence. Defines when reflection is required so retrospection happens on exceptions rather than after routine progress.'
applyTo: '**'
---

# Reflection Trigger Policy

## Intent

- Reflection is an exception handler, not a default narration layer.
- Do not trigger reflection after routine progress, ordinary green runs, or small successful edits that do not change the diagnosis of the work.
- Trigger reflection only when evidence shows failure, blockage, contradiction, retry pressure, or stalled criterion movement.

## Reflection Triggers

Run a reflection step only when at least one of the following is true:

- failed test or command evidence exists
- the slice result is blocked
- the slice escalates as `scope_delta`
- work has reached a second attempt on the same slice
- a reviewer rejects the slice or requires substantive rework
- expected evidence and observed evidence contradict each other
- the same slice re-touches any previously modified file on the next attempt without criterion movement

## What Counts As Criterion Movement

- A criterion moved when acceptance evidence, verifier output, or completion-ledger status changed in a way that reduces uncertainty.
- Re-editing the same files without changing criterion status, verifier outcome, or decision quality counts as no movement.
- For this policy, `repeated touch` means the same slice modifies at least one file that was modified in the immediately previous attempt and the new attempt does not improve criterion status, verifier outcome, or decision quality.
- Do not wait for a third similar attempt to call this a repeated-touch incident; the second no-movement touch is the trigger.

## Ownership

- Lane Supervisor owns first-failure diagnosis and the first decision about whether the event is an implementation bug, acceptance-criteria gap, verifier mismatch, repository-knowledge gap, or package-boundary problem.
- PR Manager owns retrospective capture for triggered reflections and ensures the slice record includes the triggering evidence, diagnosis, and next action.
- Memory Researcher owns durable lesson distillation only when the outcome is likely to help future slices, future PR scopes, or future agents.
- Implementer reports evidence, local lesson, and escalation status but does not introduce an always-on reflection loop.

## Required Reflection Record

When a trigger fires, capture all of the following before continuing:

- trigger type
- slice id or work package id
- target criterion or expected outcome
- expected evidence
- observed evidence
- current result: `pass`, `fail`, `blocked`, or `scope_delta`
- current root-cause hypothesis
- next strategy, escalation, or replan decision
- whether a durable memory candidate exists

This record must appear in the slice or supervisor output that handled the incident. PR Manager must also mirror a concise version into `completion-ledger.md` whenever the trigger affected PR-scope routing, retry decisions, blocker state, or criterion interpretation.

## Integration With Failed-Attempt Analysis

- If the trigger includes a failed verifier, blocked result, reviewer rejection, or evidence contradiction, classify the failure using the categories from `after-failed-attempt.instructions.md` before choosing the next action.
- Reuse that classification to drive the next owner action instead of writing a separate free-form retrospective.

## Non-Triggers

- first-pass success on a slice
- routine green-to-green edits
- minor refactors that preserve ongoing criterion progress
- ordinary completion of a bounded step with no new contradiction
- narration that only restates already visible status

## Operating Rules

- One reflection per incident is enough unless new evidence changes the diagnosis.
- Do not create a separate Reflector role for this policy.
- On first failure, Lane Supervisor handles diagnosis.
- On repeated or cross-slice patterns, PR Manager consolidates the retrospective.
- When a trigger fires, the incident record may be captured first in slice or supervisor output, but the authoritative PR-scope trace of the incident belongs in `completion-ledger.md` once PR Manager consumes it.
- Only Memory Researcher converts a reusable lesson into durable repository memory.
- If the same slice reaches a second triggered reflection, follow the existing retry and escalation policy rather than expanding local analysis indefinitely.