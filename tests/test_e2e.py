from __future__ import annotations

import unittest

from fsm_agent import FSMSession, StateEntryRecord, TransitionRecord, build_fsm, default_skill_registry
from tests.spec_fixtures import VALID_SPEC


class EndToEndTests(unittest.TestCase):
    def test_valid_spec_runs_to_completion(self) -> None:
        registry = default_skill_registry()
        fsm = build_fsm(VALID_SPEC, skill_registry=registry)
        session = FSMSession(
            fsm,
            final_goal='Deliver a validated answer to the user',
            skill_registry=registry,
        )

        first_event = session.trace[0]
        self.assertIsInstance(first_event, StateEntryRecord)
        assert isinstance(first_event, StateEntryRecord)
        self.assertIn('Stay aligned with the explicit final goal', first_event.instructions[1])

        session.context.data['notes'] = 'Request captured.'
        session.advance(to_state='plan')

        session.context.data['plan_ready'] = True
        session.advance(to_state='execute')

        session.context.data['result'] = 'Reference implementation and tests.'
        session.context.mark_goal_complete()
        final_entry = session.advance(to_state='done')

        self.assertEqual(final_entry.state, 'done')
        self.assertTrue(session.is_complete())

        transitions = [event for event in session.trace if isinstance(event, TransitionRecord)]
        self.assertEqual(len(transitions), 3)
        self.assertEqual(
            transitions[-1].guidance,
            'Package the result, confirm the final goal, and close the workflow.',
        )
        self.assertIn(
            'Only close the workflow once the explicit final goal is marked complete.',
            transitions[-1].applied_instructions,
        )

        states = [event for event in session.trace if isinstance(event, StateEntryRecord)]
        self.assertEqual([state.state for state in states], ['intake', 'plan', 'execute', 'done'])


if __name__ == '__main__':
    unittest.main()
