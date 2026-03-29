from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from .errors import GoalMismatchError, TransitionGuardError, TransitionSelectionError, UnknownSkillError
from .models import CompiledFSM, CompiledState, CompiledTransition, canonical_name
from .skills import Skill, default_skill_registry


@dataclass
class ExecutionContext:
    """Mutable runtime context carried across the FSM execution."""

    final_goal: str
    data: dict[str, Any] = field(default_factory=dict)
    goal_status: str = 'pending'

    def mark_goal_complete(self) -> None:
        self.goal_status = 'complete'


@dataclass(frozen=True)
class StateEntryRecord:
    state: str
    state_key: str
    goal: str
    instructions: tuple[str, ...]
    state_skills: tuple[str, ...]


@dataclass(frozen=True)
class TransitionRecord:
    transition_id: str
    from_state: str
    from_state_key: str
    to_state: str
    to_state_key: str
    condition: str
    guidance: str
    skills: tuple[str, ...]
    applied_instructions: tuple[str, ...]


@dataclass(frozen=True)
class TransitionOption:
    transition_id: str
    to_state: str
    condition: str
    guidance: str
    skills: tuple[str, ...]
    allowed: bool
    blocked_by: tuple[str, ...] = ()
    preview_instructions: tuple[str, ...] = ()


class FSMSession:
    """Runtime executor that enforces transitions against a validated FSM."""

    def __init__(
        self,
        fsm: CompiledFSM,
        *,
        final_goal: str,
        skill_registry: Mapping[str, Skill] | None = None,
        initial_data: Mapping[str, Any] | None = None,
    ) -> None:
        passed_goal = ' '.join(final_goal.strip().split())
        if not passed_goal:
            raise GoalMismatchError('An explicit final_goal must be passed to the runtime session.')
        if passed_goal != fsm.final_goal:
            raise GoalMismatchError(
                f'Passed final_goal {passed_goal!r} does not match compiled FSM goal {fsm.final_goal!r}.'
            )

        self.fsm = fsm
        self.context = ExecutionContext(final_goal=fsm.final_goal, data=dict(initial_data or {}))
        self._skill_registry = dict(skill_registry) if skill_registry is not None else default_skill_registry()
        self._current_state = fsm.state_map[fsm.initial_state_key]
        self.trace: list[StateEntryRecord | TransitionRecord] = []
        self._enter_state(self._current_state)

    @property
    def current_state(self) -> CompiledState:
        return self._current_state

    def transition_options(self) -> tuple[TransitionOption, ...]:
        options: list[TransitionOption] = []
        for transition in self.current_state.transitions:
            blocked_by: list[str] = []
            try:
                applied_instructions, guard_errors = self._evaluate_transition_skills(
                    transition,
                    enforce_guards=False,
                )
                blocked_by.extend(guard_errors)
            except UnknownSkillError as exc:
                blocked_by.append(str(exc))
                applied_instructions = ()
            options.append(
                TransitionOption(
                    transition_id=transition.transition_id,
                    to_state=transition.to_state,
                    condition=transition.condition,
                    guidance=transition.guidance,
                    skills=transition.skills,
                    allowed=not blocked_by,
                    blocked_by=tuple(blocked_by),
                    preview_instructions=applied_instructions,
                )
            )
        return tuple(options)

    def advance(
        self,
        *,
        transition_id: str | None = None,
        to_state: str | None = None,
        condition: str | None = None,
    ) -> StateEntryRecord:
        transition = self._select_transition(transition_id=transition_id, to_state=to_state, condition=condition)
        applied_instructions, _ = self._evaluate_transition_skills(transition, enforce_guards=True)
        self.trace.append(
            TransitionRecord(
                transition_id=transition.transition_id,
                from_state=transition.from_state,
                from_state_key=transition.from_state_key,
                to_state=transition.to_state,
                to_state_key=transition.to_state_key,
                condition=transition.condition,
                guidance=transition.guidance,
                skills=transition.skills,
                applied_instructions=applied_instructions,
            )
        )
        self._current_state = self.fsm.state_map[transition.to_state_key]
        return self._enter_state(self._current_state)

    def is_complete(self) -> bool:
        return (
            self.current_state.key in self.fsm.terminal_state_keys
            and self.context.goal_status == 'complete'
            and self.context.final_goal == self.fsm.final_goal
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            'current_state': self.current_state.name,
            'current_state_key': self.current_state.key,
            'goal_status': self.context.goal_status,
            'final_goal': self.context.final_goal,
            'data': dict(self.context.data),
            'is_complete': self.is_complete(),
            'transition_options': [asdict(option) for option in self.transition_options()],
            'trace': [asdict(event) for event in self.trace],
        }

    def _enter_state(self, state: CompiledState) -> StateEntryRecord:
        instructions = list(state.instructions)
        for skill_name in state.state_skills:
            skill = self._resolve_skill(skill_name)
            if skill.state_instructions is not None:
                instructions.extend(self._normalize_lines(skill.state_instructions(self.context, state)))
        entry = StateEntryRecord(
            state=state.name,
            state_key=state.key,
            goal=self.context.final_goal,
            instructions=tuple(instructions),
            state_skills=state.state_skills,
        )
        self.trace.append(entry)
        return entry

    def _select_transition(
        self,
        *,
        transition_id: str | None,
        to_state: str | None,
        condition: str | None,
    ) -> CompiledTransition:
        if transition_id is None and to_state is None:
            raise TransitionSelectionError('Provide either transition_id or to_state to advance the session.')

        matches = list(self.current_state.transitions)
        if transition_id is not None:
            matches = [transition for transition in matches if transition.transition_id == transition_id]
        if to_state is not None:
            target_key = canonical_name(to_state)
            matches = [transition for transition in matches if transition.to_state_key == target_key]
        if condition is not None:
            expected_condition = ' '.join(condition.strip().split())
            matches = [transition for transition in matches if transition.condition == expected_condition]

        if not matches:
            raise TransitionSelectionError(
                f"No legal transition found from state '{self.current_state.name}' for the supplied selector."
            )
        if len(matches) > 1:
            ids = ', '.join(transition.transition_id for transition in matches)
            raise TransitionSelectionError(
                f"Transition selector is ambiguous from state '{self.current_state.name}'. Matching ids: {ids}."
            )
        return matches[0]

    def _resolve_skill(self, skill_name: str) -> Skill:
        skill = self._skill_registry.get(skill_name)
        if skill is None:
            raise UnknownSkillError(f"Unknown skill '{skill_name}'.")
        return skill

    def _evaluate_transition_skills(
        self,
        transition: CompiledTransition,
        *,
        enforce_guards: bool,
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        instructions: list[str] = []
        guard_errors: list[str] = []
        for skill_name in transition.skills:
            skill = self._resolve_skill(skill_name)
            if skill.guard is not None:
                try:
                    skill.guard(self.context, transition)
                except TransitionGuardError as exc:
                    if enforce_guards:
                        raise
                    guard_errors.append(str(exc))
            if skill.transition_instructions is not None:
                instructions.extend(self._normalize_lines(skill.transition_instructions(self.context, transition)))
        return tuple(instructions), tuple(guard_errors)

    @staticmethod
    def _normalize_lines(lines: Sequence[str]) -> list[str]:
        normalized: list[str] = []
        for line in lines:
            cleaned = ' '.join(str(line).strip().split())
            if cleaned:
                normalized.append(cleaned)
        return normalized
