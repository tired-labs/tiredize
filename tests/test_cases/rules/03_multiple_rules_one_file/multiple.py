from tiredize.linter.types import RuleResult
from tiredize.markdown.types.document import Document
from tiredize.types import Position
from typing import Any, Dict, List


def validate_first(
    document: Document,
    config: Dict[str, Any],
) -> List[RuleResult]:
    """
    Simple example rule (#1) used for testing.
    """
    result = RuleResult(
        message="This is test rule #1.",
        position=Position(
            line=111,
            offset=11,
            length=11
        ),
        rule_id="multiple.first"
    )
    return [result]


def validate_second(
    document: Document,
    config: Dict[str, Any],
) -> List[RuleResult]:
    """
    Simple example rule (#2) used for testing.
    """
    result = RuleResult(
        message="This is test rule #2.",
        position=Position(
            line=222,
            offset=22,
            length=22
        ),
        rule_id="multiple.second"
    )
    return [result]
