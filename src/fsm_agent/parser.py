from __future__ import annotations

import re
from textwrap import dedent
from typing import cast

from .errors import ParseError
from .models import FSMDefinition, StateDefinition, TransitionDefinition, split_csv

_TOP_LEVEL_RE = re.compile(r'^(goal|final_goal|initial_state|terminal_states):\s*(.*)$')
_STATE_RE = re.compile(r'^state:\s*(.+)$')
_SECTION_RE = re.compile(r'^(instructions|state_skills|transitions):\s*(.*)$')
_BULLET_RE = re.compile(r'^-\s+(.+)$')
_TRANSITION_START_RE = re.compile(r'^-\s+to:\s*(.+)$')
_TRANSITION_FIELD_RE = re.compile(r'^(when|guidance|skills):\s*(.*)$')


def parse_fsm(spec_text: str) -> FSMDefinition:
    """Parse a constrained natural-language FSM authoring format."""
    normalized_text = dedent(spec_text).strip('\n')
    if not normalized_text.strip():
        raise ParseError('FSM specification is empty.')

    final_goal = ''
    initial_state = ''
    terminal_states: tuple[str, ...] = ()
    states: list[StateDefinition] = []
    seen_top_level: set[str] = set()

    current_state_name: str | None = None
    current_instructions: list[str] = []
    current_state_skills: list[str] = []
    current_transitions: list[TransitionDefinition] = []
    current_transition: dict[str, object] | None = None
    current_section: str | None = None

    def finalize_transition() -> None:
        nonlocal current_transition
        if current_transition is None:
            return
        raw_skills = cast(list[str] | tuple[str, ...], current_transition.get('skills', ()))
        current_transitions.append(
            TransitionDefinition(
                to_state=str(current_transition.get('to_state', '')),
                condition=str(current_transition.get('condition', '')),
                guidance=str(current_transition.get('guidance', '')),
                skills=tuple(raw_skills),
            )
        )
        current_transition = None

    def finalize_state() -> None:
        nonlocal current_state_name, current_instructions, current_state_skills, current_transitions, current_section
        if current_state_name is None:
            return
        finalize_transition()
        states.append(
            StateDefinition(
                name=current_state_name,
                instructions=tuple(current_instructions),
                state_skills=tuple(current_state_skills),
                transitions=tuple(current_transitions),
            )
        )
        current_state_name = None
        current_instructions = []
        current_state_skills = []
        current_transitions = []
        current_section = None

    for line_no, raw_line in enumerate(normalized_text.splitlines(), start=1):
        if not raw_line.strip() or raw_line.strip().startswith('#'):
            continue
        leading = raw_line[: len(raw_line) - len(raw_line.lstrip(' '))]
        if '\t' in leading:
            raise ParseError('Tabs are not allowed for indentation; use spaces only.', line_no=line_no)
        indent = len(leading)
        if indent % 2 != 0:
            raise ParseError('Indentation must use multiples of two spaces.', line_no=line_no)
        text = raw_line.strip()

        if indent == 0:
            state_match = _STATE_RE.match(text)
            if state_match:
                finalize_state()
                current_state_name = state_match.group(1).strip()
                if not current_state_name:
                    raise ParseError('State names cannot be empty.', line_no=line_no)
                continue

            finalize_state()
            top_match = _TOP_LEVEL_RE.match(text)
            if not top_match:
                raise ParseError(
                    "Expected a top-level field ('goal', 'initial_state', 'terminal_states') or 'state: <name>'.",
                    line_no=line_no,
                )
            key, value = top_match.groups()
            canonical_key = 'final_goal' if key in {'goal', 'final_goal'} else key
            if canonical_key in seen_top_level:
                raise ParseError(f"Duplicate top-level field '{canonical_key}'.", line_no=line_no)
            seen_top_level.add(canonical_key)
            if canonical_key == 'final_goal':
                final_goal = value.strip()
            elif canonical_key == 'initial_state':
                initial_state = value.strip()
            elif canonical_key == 'terminal_states':
                terminal_states = split_csv(value)
            continue

        if current_state_name is None:
            raise ParseError('Indented content must appear inside a state block.', line_no=line_no)

        if indent == 2:
            finalize_transition()
            section_match = _SECTION_RE.match(text)
            if not section_match:
                raise ParseError(
                    "Expected one of 'instructions:', 'state_skills:', or 'transitions:' inside a state block.",
                    line_no=line_no,
                )
            section_name, inline_value = section_match.groups()
            current_section = section_name
            if section_name == 'instructions' and inline_value:
                raise ParseError("'instructions:' must be followed by indented bullet items.", line_no=line_no)
            if section_name == 'transitions' and inline_value:
                raise ParseError("'transitions:' must be followed by indented transition items.", line_no=line_no)
            if section_name == 'state_skills' and inline_value:
                current_state_skills.extend(split_csv(inline_value))
            continue

        if indent == 4:
            if current_section == 'instructions':
                bullet_match = _BULLET_RE.match(text)
                if not bullet_match:
                    raise ParseError('Instruction entries must use bullet syntax like `- do work`.', line_no=line_no)
                current_instructions.append(bullet_match.group(1).strip())
                continue

            if current_section == 'state_skills':
                bullet_match = _BULLET_RE.match(text)
                if not bullet_match:
                    raise ParseError(
                        'State skills must use bullet syntax or comma-separated inline values.',
                        line_no=line_no,
                    )
                current_state_skills.append(bullet_match.group(1).strip())
                continue

            if current_section == 'transitions':
                transition_match = _TRANSITION_START_RE.match(text)
                if not transition_match:
                    raise ParseError('Transition entries must start with `- to: <state>`.', line_no=line_no)
                finalize_transition()
                current_transition = {
                    'to_state': transition_match.group(1).strip(),
                    'condition': '',
                    'guidance': '',
                    'skills': [],
                }
                continue

            raise ParseError('Unexpected indentation or section structure.', line_no=line_no)

        if indent == 6:
            if current_section != 'transitions' or current_transition is None:
                raise ParseError('Transition fields must appear under a `- to:` transition entry.', line_no=line_no)
            field_match = _TRANSITION_FIELD_RE.match(text)
            if not field_match:
                raise ParseError('Expected transition field `when:`, `guidance:`, or `skills:`.', line_no=line_no)
            field_name, value = field_match.groups()
            if field_name == 'skills':
                existing_skills = cast(list[str] | tuple[str, ...], current_transition.get('skills', ()))
                current_transition['skills'] = list(existing_skills) + list(split_csv(value))
            else:
                storage_key = 'condition' if field_name == 'when' else field_name
                existing = str(current_transition.get(storage_key, ''))
                if existing:
                    raise ParseError(f"Duplicate transition field '{field_name}'.", line_no=line_no)
                current_transition[storage_key] = value.strip()
            continue

        raise ParseError('Unexpected indentation depth; use 0/2/4/6 spaces only.', line_no=line_no)

    finalize_state()
    return FSMDefinition(
        final_goal=final_goal,
        initial_state=initial_state,
        terminal_states=terminal_states,
        states=tuple(states),
    )
