from __future__ import annotations


class FSMError(Exception):
    """Base class for framework-specific errors."""


class ParseError(FSMError):
    """Raised when a natural-language FSM specification cannot be normalized."""

    def __init__(self, message: str, *, line_no: int | None = None) -> None:
        self.message = message
        self.line_no = line_no
        if line_no is not None:
            super().__init__(f'Parse error on line {line_no}: {message}')
        else:
            super().__init__(f'Parse error: {message}')


class ValidationError(FSMError):
    """Raised when a normalized FSM is semantically invalid."""

    def __init__(self, errors: list[str] | tuple[str, ...]) -> None:
        self.errors = tuple(errors)
        message = 'FSM validation failed:\n- ' + '\n- '.join(self.errors)
        super().__init__(message)


class GoalMismatchError(FSMError):
    """Raised when the runtime goal is absent or differs from the compiled FSM goal."""


class TransitionSelectionError(FSMError):
    """Raised when the runtime cannot resolve a unique legal transition."""


class TransitionGuardError(FSMError):
    """Raised when a transition-level guard skill blocks execution."""


class UnknownSkillError(FSMError):
    """Raised when the runtime references a skill that is not registered."""
