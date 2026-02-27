# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document


def validate_hidden(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """Should not be discovered because the module is private."""
    return []
