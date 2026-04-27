---
name: "Temporary Files Usage"
description: "Use for all workflows requiring temporary file storage. Enforces project-local .tmp/ directory usage."
applyTo: "**"
---
# Temporary Files Usage Instructions

## Rule
- All temporary files must be written to `./.tmp/` directory within this repository.
- Do not use the system `/tmp` folder or any root-level temporary directories.
- The `.tmp/` directory should be created automatically if it does not exist.

## Implementation
- Initialize the `.tmp/` folder at the start of any workflow that requires temporary storage.
- Use relative paths: `.tmp/filename` rather than absolute paths.
- Clean up temporary files upon workflow completion unless explicitly retained for debugging.

## Rationale
- Keeps artifact management isolated and project-specific.
- Prevents conflicts with system temporary storage and other projects.
- Simplifies cleanup and maintains repository independence.

## Exceptions
- None. This rule applies to all agent workflows in this repository.