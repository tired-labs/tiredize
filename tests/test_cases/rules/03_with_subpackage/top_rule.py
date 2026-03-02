# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """Top-level rule that should be discovered."""
    return []
