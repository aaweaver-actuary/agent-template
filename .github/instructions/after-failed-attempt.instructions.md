---
name: 'Required Retrospective Analysis After Any Failed Attempt'
description: 'Ensures that a detailed analysis is conducted after any failed attempt, capturing observations, results, and lessons learned.'
applyTo: '**'
---

## Failure Classification

Failures should be categorized to help identify root causes and inform future improvements.

Please categorize the failure according to one of the following types:

- incorrect package boundary
- missing repository knowledge
- unclear acceptance criteria
- verifier/test mismatch
- implementation bug
- interface/schema gap
- hidden dependency outside allowed scope
- non-reproducible environment issue

## Mapping Failures to Actions

For each type of failure, the corresponding cause and recommended action are outlined below to guide the appropriate response.

### If `incorrect package boundary` is selected

- Cause of failure: Modifying files or components outside the allowed package scope.
- Recommended action: Dispatch a reviewer to examine the package boundaries, ensuring that all changes are confined to the appropriate scope.

### If `missing repository knowledge` is selected

- Cause of failure: Lack of necessary knowledge about the repository, its structure, or its contents.
- Recommended action: Dispatch a memory finder to gather the required information and provide the necessary context for resolving the issue.

### If `unclear acceptance criteria` is selected

- Cause of failure: Acceptance criteria are not clearly defined or are ambiguous.
- Recommended action: Dispatch the requirements planner or work planner to clarify the acceptance criteria.

### If `verifier/test mismatch` is selected

- Cause of failure: Mismatch between the verifier or test and the expected behavior.
- Recommended action: Dispatch a reviewer to review the tests and ensure they accurately reflect the intended functionality.

### If `implementation bug` is selected

- Cause of failure: Defect or error in the implementation of the code.
- Recommended action: Dispatch a reviewer to identify and diagnose the bug. Dispatch the implementer to correct the issue based on the reviewer's findings.

### If `interface/schema gap` is selected

- Cause of failure: Discrepancy or gap between the expected interface or schema and the actual implementation.
- Recommended action: Dispatch a memory finder to examine the interface or schema and ensure it aligns with the expected design and implementation.

### If `hidden dependency outside allowed scope` is selected

- Cause of failure: The implementation relies on a dependency that is outside the allowed scope.
- Recommended action: Dispatch a reviewer to identify the hidden dependency. Dispatch the implementer to remove or properly manage the out-of-scope dependency based on the reviewer's findings.

### If `non-reproducible environment issue` is selected

- Cause of failure: The failure occurs due to an environment that cannot be consistently reproduced.
- Recommended action: Dispatch a memory finder to investigate and record the environment setup. Dispatch the implementer to ensure that the environment can be reliably reproduced for consistent results.

When this classification is triggered by a reflection-policy incident, include the classification in the incident record returned to the supervising role and preserve the same classification when PR Manager mirrors the concise incident record into `completion-ledger.md`.