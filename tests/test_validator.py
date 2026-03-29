from __future__ import annotations

import unittest

from fsm_agent.errors import ValidationError
from fsm_agent.parser import parse_fsm
from fsm_agent.skills import default_skill_registry
from fsm_agent.validator import validate_fsm
from tests.spec_fixtures import (
    MISSING_GOAL_SPEC,
    MISSING_GUIDANCE_SPEC,
    UNKNOWN_TARGET_SPEC,
    UNREACHABLE_STATE_SPEC,
    VALID_SPEC,
)


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = default_skill_registry()

    def test_valid_spec_compiles(self) -> None:
        compiled = validate_fsm(parse_fsm(VALID_SPEC), skill_registry=self.registry)
        self.assertEqual(compiled.final_goal, 'Deliver a validated answer to the user')
        self.assertEqual(compiled.initial_state, 'intake')
        self.assertEqual(compiled.terminal_states, ('done',))
        self.assertEqual(len(compiled.states), 4)

    def test_missing_goal_fails(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_fsm(parse_fsm(MISSING_GOAL_SPEC), skill_registry=self.registry)
        self.assertIn('Missing explicit final goal.', str(ctx.exception))

    def test_missing_guidance_fails(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_fsm(parse_fsm(MISSING_GUIDANCE_SPEC), skill_registry=self.registry)
        self.assertIn('missing explicit guidance', str(ctx.exception))

    def test_unknown_transition_target_fails(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_fsm(parse_fsm(UNKNOWN_TARGET_SPEC), skill_registry=self.registry)
        self.assertIn('points to an undefined state', str(ctx.exception))

    def test_unreachable_state_fails(self) -> None:
        with self.assertRaises(ValidationError) as ctx:
            validate_fsm(parse_fsm(UNREACHABLE_STATE_SPEC), skill_registry=self.registry)
        self.assertIn('is unreachable from initial state', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
