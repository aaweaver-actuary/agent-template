---
name: 'Repository Memory Management'
description: 'Use for all project workflows that need repository memory management, record-keeping, durable discoveries, or quick reference lookup in the .memories folder.'
applyTo: '**'
---

# Repository Memory Management

## Startup Protocol

- At the start of each workflow, look for `.memories/` at the repository root.
- If `.memories/` does not exist, create it and create `.memories/00index.md` and `.memories/00template.md`.
- Treat `.memories/00index.md` as the entry point to repository memory.

## Source Of Truth Policy

- `.memories/` at the repository root is the only authoritative memory store for this repository.
- Active execution state is not repository memory truth; `request-plan.md` is the authoritative request-level planning artifact and `completion-ledger.md` is the authoritative PR-scope completion artifact.
- Architecture decision history for active planning belongs in `decision-log.md`, owned by Requirements Planner.
- Do not use `/memories/repo/`, `/memories/session/`, or any other external memory namespace as a source for repository facts, plans, or workflow decisions.
- If memory content exists outside `.memories/`, verify it against the repository, migrate the verified result into `.memories/`, and treat external copies as non-authoritative.
- If conflicting memory content exists in multiple places, `.memories/` wins after re-verification and refresh.

## Memory Structure

- Keep each memory as one atomic markdown file that answers one question or records one durable fact.
- Name memory files as plain-language questions or declarative statements, such as `How do we validate work in this project.md` or `Precommit blocks direct commits to main and runs staged checks.md`.
- Reserve `00index.md` for the memory catalog and `00template.md` for the standard memory shape.
- Keep `00index.md` updated with one-line summaries and links to each memory.

## Memory Template

- Every question or declarative-statement memory should follow the `00template.md` structure.
- Use an `## Answer` section for the quick-reference content.
- Use an `## Freshness` section with at least:
  - `Status: verified against repository`
  - `Last verified: YYYY-MM-DD`
  - `Verified from:` followed by the files, commands, or evidence checked
  - `Refresh when:` followed by the main conditions that would make the memory stale

## Roles

- Agents other than Memory Finder and Memory Researcher must not read or write `.memories/` directly.
- Use Memory Finder when you need an answer from existing repository memories.
- Use Memory Researcher when a memory is missing, stale, or needs to be created or updated.
- Memory Finder and Memory Researcher must treat `.memories/` as canonical and must not rely on `/memories/repo/` for repository truth.
- Memory Researcher memory writes are allowed only for durable categories:
  - cross-slice architectural decisions
  - durable interface contracts
  - resolved blockers likely to recur
  - environment or build constraints
  - user preferences that affect future slices

## Recording Process

- When an agent discovers durable knowledge in the allowed categories, emit a memory candidate instead of editing `.memories/` directly.
- Memory Finder should answer from existing memory when possible. If the answer is missing, uncertain, or stale according to its `## Freshness` section, it should escalate to Memory Researcher.
- Memory Researcher must verify the current answer against the repository, write or update the atomic memory file using `00template.md`, and refresh `00index.md` before returning the result.
- When migrating memory from non-canonical stores, Memory Researcher should note the migration in the updated memory and remove or deprecate duplicate external copies.

## Quality Bar

- Prefer short, high-signal memories over long narrative documents.
- Keep memory content specific, current, and easy to scan.
- Prefer a few strong bullets in `## Answer` over narrative prose.
- Keep `## Freshness` current enough that another agent can decide whether to trust the memory immediately.
- Update or replace stale memories rather than creating near-duplicate files.
