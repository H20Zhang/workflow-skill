from __future__ import annotations

import unittest

from fsm_agent import FSMSession, build_fsm, default_skill_registry
from fsm_agent.errors import GoalMismatchError, TransitionGuardError, TransitionSelectionError
from tests.spec_fixtures import AMBIGUOUS_TRANSITION_SPEC, VALID_SPEC


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = default_skill_registry()
        self.fsm = build_fsm(VALID_SPEC, skill_registry=self.registry)

    def test_goal_must_match_compiled_spec(self) -> None:
        with self.assertRaises(GoalMismatchError):
            FSMSession(self.fsm, final_goal='Different goal', skill_registry=self.registry)

    def test_invalid_out_of_order_transition_is_blocked(self) -> None:
        session = FSMSession(
            self.fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=self.registry,
        )
        with self.assertRaises(TransitionSelectionError):
            session.advance(to_state='execute')

    def test_guard_blocks_missing_notes(self) -> None:
        session = FSMSession(
            self.fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=self.registry,
        )
        with self.assertRaises(TransitionGuardError) as ctx:
            session.advance(to_state='plan')
        self.assertIn("context.data['notes']", str(ctx.exception))

    def test_guard_blocks_terminal_transition_until_goal_is_complete(self) -> None:
        session = FSMSession(
            self.fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=self.registry,
        )
        session.context.data['notes'] = 'Ready to plan.'
        session.advance(to_state='plan')
        session.context.data['plan_ready'] = True
        session.advance(to_state='execute')
        session.context.data['result'] = 'Artifact produced.'
        with self.assertRaises(TransitionGuardError) as ctx:
            session.advance(to_state='done')
        self.assertIn('marked complete', str(ctx.exception))

    def test_snapshot_reports_completion(self) -> None:
        session = FSMSession(
            self.fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=self.registry,
        )
        session.context.data['notes'] = 'Ready to plan.'
        session.advance(to_state='plan')
        session.context.data['plan_ready'] = True
        session.advance(to_state='execute')
        session.context.data['result'] = 'Artifact produced.'
        session.context.mark_goal_complete()
        session.advance(to_state='done')
        snapshot = session.snapshot()
        self.assertTrue(snapshot['is_complete'])
        self.assertEqual(snapshot['current_state'], 'done')

    def test_transition_options_surface_blocking_reasons(self) -> None:
        session = FSMSession(
            self.fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=self.registry,
        )
        options = session.transition_options()
        self.assertEqual(len(options), 1)
        self.assertFalse(options[0].allowed)
        self.assertIn("context.data['notes']", options[0].blocked_by[0])
        self.assertIn('Carry the collected notes forward', options[0].preview_instructions[0])

    def test_selector_can_be_ambiguous(self) -> None:
        ambiguous_fsm = build_fsm(AMBIGUOUS_TRANSITION_SPEC, skill_registry=self.registry)
        session = FSMSession(
            ambiguous_fsm,
            final_goal='Ambiguous selector example',
            skill_registry=self.registry,
        )
        with self.assertRaises(TransitionSelectionError):
            session.advance(to_state='execute')
        entry = session.advance(to_state='execute', condition='the fast path is acceptable')
        self.assertEqual(entry.state, 'execute')


if __name__ == '__main__':
    unittest.main()
