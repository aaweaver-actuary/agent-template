#!/usr/bin/env sh
set -eu

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
memories_dir="$repo_root/.memories"
index_file="$memories_dir/00index.md"
template_file="$memories_dir/00template.md"

mkdir -p "$memories_dir"

if [ ! -f "$template_file" ]; then
  cat > "$template_file" <<'EOF'
# Memory Template

Use this structure for question or declarative-statement memories.

```md
# <Question or declarative statement>

## Answer
- Concise quick-reference bullets only.

## Freshness
- Status: verified against repository
- Last verified: YYYY-MM-DD
- Verified from:
  - path/to/file
- Refresh when:
  - the underlying workflow, file layout, contract, or command changes
```

Guidelines:
- Keep each memory atomic and single-topic.
- Prefer a few strong bullets over prose.
- Update `## Freshness` whenever the answer is re-verified.
EOF
fi

if [ ! -f "$index_file" ]; then
  cat > "$index_file" <<'EOF'
# Repository Memory Index

This folder stores atomic quick-reference memories for future agents.

## Rules
- Start here before reading individual memories.
- Use `00template.md` when creating or updating question or declarative-statement memories.
- Each memory answers one question or records one durable repository fact.
- Memory files use plain-language question or declarative-statement names.
- Memory Finder reads from this folder. Memory Researcher verifies and writes to it.

## Entries
- [00template.md](00template.md): template for atomic memory files and freshness signals.
EOF
fi