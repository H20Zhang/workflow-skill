from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from fsm_agent import FSMSession, build_fsm, default_skill_registry

    spec_path = ROOT / 'examples' / 'research_workflow.txt'
    actions_path = ROOT / 'examples' / 'research_workflow_actions.json'

    registry = default_skill_registry()
    fsm = build_fsm(spec_path.read_text(encoding='utf-8'), skill_registry=registry)
    session = FSMSession(
        fsm,
        final_goal='Deliver a validated answer to the user',
        skill_registry=registry,
    )

    actions = json.loads(actions_path.read_text(encoding='utf-8'))
    for action in actions:
        if 'set' in action:
            session.context.data.update(action['set'])
        if action.get('mark_goal_complete'):
            session.context.mark_goal_complete()
        if 'advance' in action:
            session.advance(**action['advance'])

    print(json.dumps(session.snapshot(), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
