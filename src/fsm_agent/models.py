from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field

_CANONICAL_NAME_RE = re.compile(r'[^a-z0-9]+')
_WHITESPACE_RE = re.compile(r'\s+')


def canonical_name(value: str) -> str:
    normalized = _CANONICAL_NAME_RE.sub('_', value.strip().lower()).strip('_')
    if not normalized:
        raise ValueError(f'Cannot canonicalize an empty name from {value!r}.')
    return normalized


def normalize_text(value: str) -> str:
    return _WHITESPACE_RE.sub(' ', value.strip())


def split_csv(value: str) -> tuple[str, ...]:
    if not value.strip():
        return ()
    return tuple(part.strip() for part in value.split(',') if part.strip())


def dedupe_preserving_order(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return tuple(ordered)


@dataclass(frozen=True)
class TransitionDefinition:
    to_state: str
    guidance: str
    condition: str = ''
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateDefinition:
    name: str
    instructions: tuple[str, ...] = ()
    state_skills: tuple[str, ...] = ()
    transitions: tuple[TransitionDefinition, ...] = ()


@dataclass(frozen=True)
class FSMDefinition:
    final_goal: str
    initial_state: str
    terminal_states: tuple[str, ...]
    states: tuple[StateDefinition, ...]


@dataclass(frozen=True)
class CompiledTransition:
    transition_id: str
    from_state: str
    from_state_key: str
    to_state: str
    to_state_key: str
    guidance: str
    condition: str = ''
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompiledState:
    name: str
    key: str
    instructions: tuple[str, ...] = ()
    state_skills: tuple[str, ...] = ()
    transitions: tuple[CompiledTransition, ...] = ()


@dataclass(frozen=True)
class CompiledFSM:
    final_goal: str
    initial_state: str
    initial_state_key: str
    terminal_states: tuple[str, ...]
    terminal_state_keys: frozenset[str]
    states: tuple[CompiledState, ...]
    state_map: Mapping[str, CompiledState] = field(default_factory=dict)
