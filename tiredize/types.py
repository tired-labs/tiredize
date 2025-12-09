from dataclasses import dataclass


@dataclass(frozen=False)
class RuleResult:
    position: "Position"
    rule_id: str
    message: str


@dataclass(frozen=False)
class Position:
    line: int
    offset: int
    length: int
