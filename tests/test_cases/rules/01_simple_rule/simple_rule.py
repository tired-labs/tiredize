# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Simple example rule used for testing.
    """
    result = RuleResult(
        message="This is a simple test rule.",
        position=Position(
            offset=50,
            length=15
        ),
        rule_id="simple_rule"
    )
    return [result]
