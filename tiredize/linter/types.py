from dataclasses import dataclass
from tiredize.types import Position


@dataclass(frozen=False)
class RuleResult:
    position: "Position"
    rule_id: str | None
    message: str
