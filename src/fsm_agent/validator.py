from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Mapping
from types import MappingProxyType

from .errors import ValidationError
from .models import (
    CompiledFSM,
    CompiledState,
    CompiledTransition,
    FSMDefinition,
    StateDefinition,
    canonical_name,
    dedupe_preserving_order,
    normalize_text,
)
from .skills import Skill


def validate_fsm(definition: FSMDefinition, *, skill_registry: Mapping[str, Skill] | None = None) -> CompiledFSM:
    """Validate and compile a normalized FSM definition into an indexed runtime form."""
    errors: list[str] = []
    registry = dict(skill_registry) if skill_registry is not None else None

    final_goal = normalize_text(definition.final_goal)
    if not final_goal:
        errors.append('Missing explicit final goal.')

    if not normalize_text(definition.initial_state):
        errors.append('Missing initial_state.')

    if not definition.terminal_states:
        errors.append('At least one terminal state is required.')

    if not definition.states:
        errors.append('At least one state definition is required.')

    raw_states_by_key: dict[str, StateDefinition] = {}
    ordered_state_keys: list[str] = []

    for state in definition.states:
        state_name = normalize_text(state.name)
        if not state_name:
            errors.append('State names must be non-empty.')
            continue
        try:
            state_key = canonical_name(state_name)
        except ValueError:
            errors.append(f'State name {state.name!r} is not canonicalizable.')
            continue
        if state_key in raw_states_by_key:
            original_state = raw_states_by_key[state_key]
            errors.append(
                'Duplicate state '
                f"'{state_name}' collides with '"
                f"{normalize_text(original_state.name)}' after normalization."
            )
            continue
        raw_states_by_key[state_key] = state
        ordered_state_keys.append(state_key)
        if registry is not None:
            for skill_name in state.state_skills:
                if skill_name not in registry:
                    errors.append(f"State '{state_name}' references unknown skill '{skill_name}'.")

    initial_state_key: str | None = None
    initial_state_name = normalize_text(definition.initial_state)
    if initial_state_name:
        try:
            initial_state_key = canonical_name(initial_state_name)
        except ValueError:
            errors.append('initial_state is not canonicalizable.')
            initial_state_key = None
        else:
            if initial_state_key not in raw_states_by_key:
                errors.append(f"Initial state '{initial_state_name}' is undefined.")

    terminal_state_keys: set[str] = set()
    normalized_terminal_states: list[str] = []
    seen_terminals: set[str] = set()
    for terminal_name_raw in definition.terminal_states:
        terminal_name = normalize_text(terminal_name_raw)
        if not terminal_name:
            errors.append('Terminal state names must be non-empty.')
            continue
        try:
            terminal_key = canonical_name(terminal_name)
        except ValueError:
            errors.append(f"Terminal state '{terminal_name_raw}' is not canonicalizable.")
            continue
        if terminal_key in seen_terminals:
            errors.append(f"Terminal state '{terminal_name}' is duplicated.")
            continue
        seen_terminals.add(terminal_key)
        normalized_terminal_states.append(terminal_name)
        if terminal_key not in raw_states_by_key:
            errors.append(f"Terminal state '{terminal_name}' is undefined.")
            continue
        terminal_state_keys.add(terminal_key)

    compiled_transitions_by_state: dict[str, list[CompiledTransition]] = {key: [] for key in ordered_state_keys}
    reference_errors = False

    for state_key in ordered_state_keys:
        state = raw_states_by_key[state_key]
        state_name = normalize_text(state.name)
        if state_key in terminal_state_keys and state.transitions:
            errors.append(f"Terminal state '{state_name}' must not define outgoing transitions.")
        if state_key not in terminal_state_keys and not state.transitions:
            errors.append(f"Non-terminal state '{state_name}' must define at least one outgoing transition.")

        seen_edges: set[tuple[str, str, str]] = set()
        for index, transition in enumerate(state.transitions, start=1):
            target_name = normalize_text(transition.to_state)
            if not target_name:
                errors.append(f"State '{state_name}' has a transition with an empty target state.")
                reference_errors = True
                continue
            try:
                target_key = canonical_name(target_name)
            except ValueError:
                errors.append(f"Transition '{state_name} -> {transition.to_state}' has an invalid target name.")
                reference_errors = True
                continue
            if target_key not in raw_states_by_key:
                errors.append(f"Transition '{state_name} -> {target_name}' points to an undefined state.")
                reference_errors = True
                continue

            target_state = raw_states_by_key[target_key]
            condition = normalize_text(transition.condition)
            guidance = normalize_text(transition.guidance)
            if not guidance:
                errors.append(
                    f"Transition '{state_name} -> {normalize_text(target_state.name)}' is missing explicit guidance."
                )
            dedup_key = (state_key, target_key, condition.lower())
            if dedup_key in seen_edges:
                printable_condition = condition if condition else '<none>'
                errors.append(
                    'Duplicate transition '
                    f"'{state_name} -> {normalize_text(target_state.name)}' "
                    f"with condition '{printable_condition}'."
                )
            else:
                seen_edges.add(dedup_key)

            transition_skills = dedupe_preserving_order([skill.strip() for skill in transition.skills if skill.strip()])
            if registry is not None:
                for skill_name in transition_skills:
                    if skill_name not in registry:
                        errors.append(
                            'Transition '
                            f"'{state_name} -> {normalize_text(target_state.name)}' "
                            f"references unknown skill '{skill_name}'."
                        )

            compiled_transitions_by_state[state_key].append(
                CompiledTransition(
                    transition_id=f'{state_key}__t{index}',
                    from_state=state_name,
                    from_state_key=state_key,
                    to_state=normalize_text(target_state.name),
                    to_state_key=target_key,
                    guidance=guidance,
                    condition=condition,
                    skills=transition_skills,
                )
            )

    if initial_state_key is not None and terminal_state_keys and raw_states_by_key and not reference_errors:
        graph: dict[str, tuple[str, ...]] = {
            state_key: tuple(transition.to_state_key for transition in compiled_transitions_by_state[state_key])
            for state_key in ordered_state_keys
        }
        reachable = _forward_reachability(initial_state_key, graph)
        for state_key in ordered_state_keys:
            if state_key not in reachable:
                errors.append(
                    'State '
                    f"'{normalize_text(raw_states_by_key[state_key].name)}' "
                    f"is unreachable from initial state '{initial_state_name}'."
                )

        reverse_graph: dict[str, set[str]] = defaultdict(set)
        for source_key, targets in graph.items():
            for target_key in targets:
                reverse_graph[target_key].add(source_key)
        can_reach_terminal = _reverse_reachability(terminal_state_keys, reverse_graph)
        if not any(state_key in terminal_state_keys for state_key in reachable):
            errors.append(f"No terminal state is reachable from initial state '{initial_state_name}'.")
        for state_key in reachable:
            if state_key not in terminal_state_keys and state_key not in can_reach_terminal:
                errors.append(
                    'Reachable non-terminal state '
                    f"'{normalize_text(raw_states_by_key[state_key].name)}' "
                    'cannot reach any terminal state.'
                )

    if errors:
        raise ValidationError(errors)

    compiled_states: list[CompiledState] = []
    state_map: dict[str, CompiledState] = {}
    for state_key in ordered_state_keys:
        state = raw_states_by_key[state_key]
        compiled_state = CompiledState(
            name=normalize_text(state.name),
            key=state_key,
            instructions=tuple(normalize_text(item) for item in state.instructions if normalize_text(item)),
            state_skills=dedupe_preserving_order([skill.strip() for skill in state.state_skills if skill.strip()]),
            transitions=tuple(compiled_transitions_by_state[state_key]),
        )
        compiled_states.append(compiled_state)
        state_map[state_key] = compiled_state

    assert initial_state_key is not None
    normalized_terminal_names = tuple(state_map[canonical_name(name)].name for name in normalized_terminal_states)
    return CompiledFSM(
        final_goal=final_goal,
        initial_state=state_map[initial_state_key].name,
        initial_state_key=initial_state_key,
        terminal_states=normalized_terminal_names,
        terminal_state_keys=frozenset(terminal_state_keys),
        states=tuple(compiled_states),
        state_map=MappingProxyType(state_map),
    )


def _forward_reachability(start_key: str, graph: Mapping[str, tuple[str, ...]]) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([start_key])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(graph.get(current, ()))
    return visited


def _reverse_reachability(start_keys: set[str], reverse_graph: Mapping[str, set[str]]) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque(start_keys)
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        queue.extend(reverse_graph.get(current, ()))
    return visited
