from dataclasses import dataclass


@dataclass
class RuleResult:
    position: "Position"
    rule_id: str
    message: str


@dataclass
class Position:
    line: int
    offset: int
    length: int
