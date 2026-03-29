from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .errors import TransitionGuardError

if TYPE_CHECKING:
    from .models import CompiledState, CompiledTransition
    from .runtime import ExecutionContext

StateInstructionFn = Callable[['ExecutionContext', 'CompiledState'], Sequence[str]]
TransitionInstructionFn = Callable[['ExecutionContext', 'CompiledTransition'], Sequence[str]]
GuardFn = Callable[['ExecutionContext', 'CompiledTransition'], None]


@dataclass(frozen=True)
class Skill:
    """Reusable guidance and optional guard logic attached to states or transitions."""

    name: str
    description: str = ''
    state_instructions: StateInstructionFn | None = None
    transition_instructions: TransitionInstructionFn | None = None
    guard: GuardFn | None = None


def default_skill_registry() -> dict[str, Skill]:
    """Sample skill set used by the reference implementation and tests."""

    def require_goal_alignment_state(context: ExecutionContext, state: CompiledState) -> Sequence[str]:
        return (f'Stay aligned with the explicit final goal: {context.final_goal}',)

    def collect_evidence_state(context: ExecutionContext, state: CompiledState) -> Sequence[str]:
        return ('Capture supporting notes in context.data["notes"] before leaving this phase.',)

    def require_notes_guard(context: ExecutionContext, transition: CompiledTransition) -> None:
        if not context.data.get('notes'):
            raise TransitionGuardError(
                f"Transition '{transition.transition_id}' requires context.data['notes'] to be populated."
            )

    def require_notes_transition(context: ExecutionContext, transition: CompiledTransition) -> Sequence[str]:
        return ('Carry the collected notes forward into the next phase.',)

    def require_plan_ready_guard(context: ExecutionContext, transition: CompiledTransition) -> None:
        if context.data.get('plan_ready') is not True:
            raise TransitionGuardError(
                f"Transition '{transition.transition_id}' requires context.data['plan_ready'] == True."
            )

    def require_plan_ready_transition(context: ExecutionContext, transition: CompiledTransition) -> Sequence[str]:
        return ('Promote the approved plan into concrete execution work.',)

    def require_artifact_guard(context: ExecutionContext, transition: CompiledTransition) -> None:
        result = context.data.get('result')
        if result is None or (isinstance(result, str) and not result.strip()):
            raise TransitionGuardError(
                'Transition '
                f"'{transition.transition_id}' requires a non-empty result artifact "
                "in context.data['result']."
            )

    def require_artifact_transition(context: ExecutionContext, transition: CompiledTransition) -> Sequence[str]:
        return ('Carry the produced artifact into the terminal phase.',)

    def require_goal_complete_guard(context: ExecutionContext, transition: CompiledTransition) -> None:
        if context.goal_status != 'complete':
            raise TransitionGuardError(
                f"Transition '{transition.transition_id}' requires the final goal to be marked complete."
            )

    def require_goal_complete_transition(context: ExecutionContext, transition: CompiledTransition) -> Sequence[str]:
        return ('Only close the workflow once the explicit final goal is marked complete.',)

    return {
        'require_goal_alignment': Skill(
            name='require_goal_alignment',
            description='Reinforce alignment between the active phase and the explicit final goal.',
            state_instructions=require_goal_alignment_state,
        ),
        'collect_evidence': Skill(
            name='collect_evidence',
            description='Collect supporting evidence before moving to another phase.',
            state_instructions=collect_evidence_state,
        ),
        'require_notes': Skill(
            name='require_notes',
            description='Require captured notes before transitioning into planning.',
            transition_instructions=require_notes_transition,
            guard=require_notes_guard,
        ),
        'require_plan_ready': Skill(
            name='require_plan_ready',
            description='Require an explicit plan-ready signal before execution.',
            transition_instructions=require_plan_ready_transition,
            guard=require_plan_ready_guard,
        ),
        'require_artifact': Skill(
            name='require_artifact',
            description='Require a non-empty result artifact before completion.',
            transition_instructions=require_artifact_transition,
            guard=require_artifact_guard,
        ),
        'require_goal_complete': Skill(
            name='require_goal_complete',
            description='Require the final goal to be marked complete before entering a terminal state.',
            transition_instructions=require_goal_complete_transition,
            guard=require_goal_complete_guard,
        ),
    }
