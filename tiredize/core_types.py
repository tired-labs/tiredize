from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    offset: int
    length: int


@dataclass(frozen=False)
class RuleResult:
    position: "Position"
    rule_id: str | None
    message: str
