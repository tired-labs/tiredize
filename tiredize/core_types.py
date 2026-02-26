# Standard library
from __future__ import annotations
from dataclasses import dataclass


class RuleNotFoundError(Exception):
    """Raised when a rule ID does not match any discovered rule."""
    pass


@dataclass(frozen=True)
class Position:
    offset: int
    length: int


@dataclass(frozen=False)
class RuleResult:
    position: Position
    rule_id: str | None
    message: str
