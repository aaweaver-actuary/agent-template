# How do we validate packaged CLI verification in this project?

## Answer
- Bootstrap the environment with `uv sync` from the repository root. The project is packaged through `uv` and exposes the `agent-template` console script from the synced `.venv`.
- Install the Playwright browser runtime with `./.venv/bin/playwright install chromium` before running browser-backed verification commands.
- For a focused verification bundle around the packaged CLI flow, run `./.venv/bin/pytest tests/test_cli.py tests/test_desktop_shell_verifier.py tests/test_run_once.py -q`.
- For end-to-end packaged CLI verification, run `./.venv/bin/agent-template run-once --milestone shell_boot`.
- If you want throwaway verification outputs instead of writing into `.agent_template/`, keep the same command and add `--state-path .tmp/<name>/state.json --artifacts-path .tmp/<name>/artifacts`.

## Freshness
- Status: verified against repository
- Last verified: 2026-04-27
- Verified from:
  - pyproject.toml
  - src/agent_template/cli.py
  - src/agent_template/__init__.py
  - src/agent_template/milestones/desktop_shell.yaml
  - tests/test_cli.py
  - tests/test_desktop_shell_verifier.py
  - tests/test_run_once.py
  - `uv sync`
  - `./.venv/bin/playwright install chromium`
  - `./.venv/bin/agent-template --help`
  - `./.venv/bin/pytest tests/test_cli.py tests/test_desktop_shell_verifier.py tests/test_run_once.py -q`
  - `./.venv/bin/agent-template run-once --milestone shell_boot --state-path .tmp/memory-check/state.json --artifacts-path .tmp/memory-check/artifacts`
- Refresh when:
  - `pyproject.toml` changes the packaging tool, dependency set, or console-script entry point
  - the Playwright runtime requirement or browser choice changes
  - the `run-once` CLI surface or the `shell_boot` milestone contract changes
  - the recommended focused test bundle changes