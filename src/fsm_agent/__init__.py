"""Finite-state-machine-constrained agent execution from constrained workflow specs."""

from .api import build_fsm, build_session
from .errors import (
    FSMError,
    GoalMismatchError,
    ParseError,
    TransitionGuardError,
    TransitionSelectionError,
    UnknownSkillError,
    ValidationError,
)
from .models import (
    CompiledFSM,
    CompiledState,
    CompiledTransition,
    FSMDefinition,
    StateDefinition,
    TransitionDefinition,
    canonical_name,
)
from .runtime import ExecutionContext, FSMSession, StateEntryRecord, TransitionOption, TransitionRecord
from .skills import Skill, default_skill_registry

__version__ = '0.2.0'

__all__ = [
    'FSMError',
    'ParseError',
    'ValidationError',
    'GoalMismatchError',
    'TransitionSelectionError',
    'TransitionGuardError',
    'UnknownSkillError',
    'FSMDefinition',
    'StateDefinition',
    'TransitionDefinition',
    'CompiledFSM',
    'CompiledState',
    'CompiledTransition',
    'ExecutionContext',
    'FSMSession',
    'StateEntryRecord',
    'TransitionRecord',
    'TransitionOption',
    'Skill',
    'build_fsm',
    'build_session',
    'default_skill_registry',
    'canonical_name',
    '__version__',
]
