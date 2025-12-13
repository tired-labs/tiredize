from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document
from typing import Any
from typing import Dict
from typing import List


def validate(
    document: Document,
    config: Dict[str, Any],
) -> List[RuleResult]:
    """
    Simple example rule used for testing.
    """
    result = RuleResult(
        message="This is a simple test rule.",
        position=Position(
            line=500,
            offset=50,
            length=15
        ),
        rule_id="simple_rule"
    )
    return [result]
