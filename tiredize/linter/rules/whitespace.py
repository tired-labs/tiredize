from __future__ import annotations
from tiredize.linter.types import RuleResult
from tiredize.markdown.types.document import Document
from tiredize.types import Position
from typing import Any
from typing import Dict
from typing import List


def validate_line_length(
    document: Document,
    config: Dict[str, Any],
) -> List[RuleResult]:
    """
    Flag lines that exceed a configured maximum length.

    Configuration:
        max_length: int - The maximum allowed line length.
    """
    raw_value = config.get("max_length")

    if isinstance(raw_value, int):
        max_len = raw_value
    elif isinstance(raw_value, str):
        try:
            max_len = int(raw_value)
        except ValueError:
            raise ValueError(
                "Invalid or missing 'max_line_length' configuration for "
                "validate_max_line_length rule."
            )
    else:
        raise ValueError(
            "Invalid or missing 'max_line_length' configuration for "
            "validate_max_line_length rule."
        )

    results: List[RuleResult] = []

    lines = document.string_markdown.splitlines()
    for line_number, line in enumerate(lines, start=1):
        line_length = len(line)
        if line_length <= max_len:
            continue

        overflow = line_length - max_len
        position = Position(
            line=line_number,
            offset=max_len,
            length=overflow,
        )

        results.append(
            RuleResult(
                message=(
                    f"Line {line_number} exceeds maximum length of "
                    f"{max_len} characters ({line_length} found)."
                ),
                position=position,
                rule_id="line_length.max_line_length",
            )
        )

    return results
