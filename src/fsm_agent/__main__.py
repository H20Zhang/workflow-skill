from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .api import build_fsm
from .errors import FSMError
from .runtime import FSMSession
from .skills import default_skill_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog='fsm-agent',
        description='Validate and run constrained natural-language FSM workflows.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    validate_parser = subparsers.add_parser('validate', help='Parse and validate a workflow spec.')
    validate_parser.add_argument('spec', type=Path, help='Path to the workflow specification file.')
    validate_parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON output.')

    demo_parser = subparsers.add_parser('demo', help='Run a workflow end-to-end using scripted actions.')
    demo_parser.add_argument('spec', type=Path, help='Path to the workflow specification file.')
    demo_parser.add_argument('--final-goal', required=True, help='Explicit runtime final goal.')
    demo_parser.add_argument('--actions', type=Path, required=True, help='JSON file describing runtime actions.')
    demo_parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON output.')

    args = parser.parse_args(argv)

    try:
        if args.command == 'validate':
            return _handle_validate(args.spec, emit_json=args.json)
        if args.command == 'demo':
            return _handle_demo(
                args.spec,
                final_goal=args.final_goal,
                actions_path=args.actions,
                emit_json=args.json,
            )
        parser.error(f'Unsupported command: {args.command}')
    except FSMError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (json.JSONDecodeError, OSError, ValueError, TypeError) as exc:
        print(f'Command failed: {exc}', file=sys.stderr)
        return 1
    return 0


def _handle_validate(spec_path: Path, *, emit_json: bool) -> int:
    fsm = build_fsm(spec_path.read_text(encoding='utf-8'), skill_registry=default_skill_registry())
    payload = {
        'final_goal': fsm.final_goal,
        'initial_state': fsm.initial_state,
        'terminal_states': list(fsm.terminal_states),
        'states': [
            {
                'name': state.name,
                'key': state.key,
                'state_skills': list(state.state_skills),
                'instructions': list(state.instructions),
                'transitions': [
                    {
                        'transition_id': transition.transition_id,
                        'to_state': transition.to_state,
                        'condition': transition.condition,
                        'guidance': transition.guidance,
                        'skills': list(transition.skills),
                    }
                    for transition in state.transitions
                ],
            }
            for state in fsm.states
        ],
    }
    if emit_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        terminal_states = ', '.join(fsm.terminal_states)
        print(
            f'Validated FSM with {len(fsm.states)} states; '
            f'initial state: {fsm.initial_state}; '
            f'terminal states: {terminal_states}'
        )
    return 0


def _handle_demo(spec_path: Path, *, final_goal: str, actions_path: Path, emit_json: bool) -> int:
    registry = default_skill_registry()
    fsm = build_fsm(spec_path.read_text(encoding='utf-8'), skill_registry=registry)
    session = FSMSession(fsm, final_goal=final_goal, skill_registry=registry)
    actions = _load_actions(actions_path)
    _apply_actions(session, actions)
    payload = session.snapshot()
    if emit_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = 'complete' if payload['is_complete'] else 'incomplete'
        print(f'Demo finished in state {payload["current_state"]} with status {status}.')
    return 0 if session.is_complete() else 2


def _load_actions(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(raw, list):
        raise ValueError('Actions file must contain a JSON list.')
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise ValueError(f'Action #{index} must be a JSON object.')
        normalized.append(item)
    return normalized


def _apply_actions(session: FSMSession, actions: list[dict[str, Any]]) -> None:
    for index, action in enumerate(actions, start=1):
        supported = {'set', 'mark_goal_complete', 'advance'}
        unknown = set(action) - supported
        if unknown:
            unknown_text = ', '.join(sorted(unknown))
            raise ValueError(f'Action #{index} contains unsupported keys: {unknown_text}.')
        if 'set' in action:
            set_payload = action['set']
            if not isinstance(set_payload, dict):
                raise ValueError(f'Action #{index} field "set" must be an object.')
            session.context.data.update(set_payload)
        if action.get('mark_goal_complete'):
            session.context.mark_goal_complete()
        if 'advance' in action:
            advance_payload = action['advance']
            if not isinstance(advance_payload, dict):
                raise ValueError(f'Action #{index} field "advance" must be an object.')
            session.advance(**advance_payload)


if __name__ == '__main__':
    raise SystemExit(main())
