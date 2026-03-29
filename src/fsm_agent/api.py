from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import CompiledFSM
from .parser import parse_fsm
from .runtime import FSMSession
from .skills import Skill, default_skill_registry
from .validator import validate_fsm


def build_fsm(spec_text: str, *, skill_registry: Mapping[str, Skill] | None = None) -> CompiledFSM:
    """Parse and validate a constrained natural-language FSM specification."""
    registry = dict(skill_registry) if skill_registry is not None else default_skill_registry()
    parsed = parse_fsm(spec_text)
    return validate_fsm(parsed, skill_registry=registry)


def build_session(
    spec_text: str,
    *,
    final_goal: str,
    skill_registry: Mapping[str, Skill] | None = None,
    initial_data: Mapping[str, Any] | None = None,
) -> FSMSession:
    """Compile a spec and start a runtime session immediately."""
    registry = dict(skill_registry) if skill_registry is not None else default_skill_registry()
    fsm = build_fsm(spec_text, skill_registry=registry)
    return FSMSession(
        fsm,
        final_goal=final_goal,
        skill_registry=registry,
        initial_data=initial_data,
    )
