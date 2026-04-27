from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_STATE_PATH = Path('.agent_template/state.json')
DEFAULT_ARTIFACTS_PATH = Path('.agent_template/artifacts')
DEFAULT_MILESTONE_PATH = Path(__file__).resolve().parent / 'milestones' / 'desktop_shell.yaml'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='agent-template')
    subparsers = parser.add_subparsers(dest='command', required=True)

    verify = subparsers.add_parser('verify')
    verify.add_argument('--milestone', required=True)
    verify.add_argument('--url', required=True)
    verify.add_argument('--state-path', default=str(DEFAULT_STATE_PATH))
    verify.add_argument('--artifacts-path', default=str(DEFAULT_ARTIFACTS_PATH))
    verify.add_argument('--milestone-file', default=str(DEFAULT_MILESTONE_PATH))
    verify.add_argument(
        '--headless',
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    verify.set_defaults(handler=run_verify)

    run_once = subparsers.add_parser('run-once')
    run_once.add_argument('--milestone', required=True)
    run_once.add_argument('--url')
    run_once.add_argument('--state-path', default=str(DEFAULT_STATE_PATH))
    run_once.add_argument('--artifacts-path', default=str(DEFAULT_ARTIFACTS_PATH))
    run_once.add_argument('--milestone-file', default=str(DEFAULT_MILESTONE_PATH))
    run_once.add_argument(
        '--headless',
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    run_once.set_defaults(handler=run_run_once)

    return parser


def run_verify(args: argparse.Namespace) -> int:
    from .browser.playwright_runner import PlaywrightRunner
    from .ledger.reflection import build_reflection_record
    from .ledger.state_store import StateStore
    from .models import RunState
    from .runtime.artifact_store import ArtifactStore
    from .verifiers.desktop_shell import DesktopShellVerifier

    state = RunState(
        objective=f'verify {args.milestone}',
        repo_path=str(Path.cwd()),
        milestone_id=args.milestone,
    )

    store = ArtifactStore(Path(args.artifacts_path))
    runner = PlaywrightRunner(store, state.run_id)
    runner.start(headless=args.headless)

    try:
        verifier = DesktopShellVerifier(runner, milestone_path=Path(args.milestone_file))
        result = verifier.verify(args.milestone, args.url)
        state.current_score = result.score
        state.artifacts.extend(result.artifacts)

        if not result.passed:
            state.no_progress_count += 1
            state.last_reflection = build_reflection_record(
                trigger_type='failed_verifier',
                slice_id='verify-command',
                milestone_result=result,
                target=args.milestone,
                classification='verification_failure',
                issue_kind='code',
                issue_subtype='missing_ui',
                touched_files=[],
                next_strategy=[
                    'inspect milestone selectors',
                    'inspect missing UI elements',
                    'check browser console errors',
                ],
            )

        StateStore(Path(args.state_path)).save(state)
        print(result.model_dump_json(indent=2))
    finally:
        runner.close()

    return 0 if result.passed else 1


def run_run_once(args: argparse.Namespace) -> int:
    from .runtime.run_once import RunOnceRequest, run_once

    outcome = run_once(
        RunOnceRequest(
            milestone_id=args.milestone,
            repo_path=Path.cwd(),
            state_path=Path(args.state_path),
            artifacts_path=Path(args.artifacts_path),
            milestone_file=Path(args.milestone_file),
            url=args.url,
            headless=args.headless,
        )
    )
    print(outcome.result.model_dump_json(indent=2))
    return outcome.exit_code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == '__main__':
    raise SystemExit(main())
