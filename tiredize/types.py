from dataclasses import dataclass


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    line: int
    message: str
