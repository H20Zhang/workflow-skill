from __future__ import annotations

import unittest

from fsm_agent.errors import ParseError
from fsm_agent.parser import parse_fsm
from tests.spec_fixtures import MALFORMED_SPEC, VALID_SPEC


class ParserTests(unittest.TestCase):
    def test_parse_valid_spec(self) -> None:
        parsed = parse_fsm(VALID_SPEC)
        self.assertEqual(parsed.final_goal, 'Deliver a validated answer to the user')
        self.assertEqual(parsed.initial_state, 'intake')
        self.assertEqual(parsed.terminal_states, ('done',))
        self.assertEqual(len(parsed.states), 4)
        self.assertEqual(parsed.states[0].name, 'intake')
        self.assertEqual(parsed.states[0].state_skills, ('require_goal_alignment', 'collect_evidence'))
        self.assertEqual(parsed.states[0].transitions[0].to_state, 'plan')
        self.assertEqual(
            parsed.states[0].transitions[0].guidance,
            'Turn the captured notes into a concrete plan for the planning phase.',
        )

    def test_rejects_malformed_instruction_block(self) -> None:
        with self.assertRaises(ParseError) as ctx:
            parse_fsm(MALFORMED_SPEC)
        self.assertIn('Instruction entries must use bullet syntax', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
