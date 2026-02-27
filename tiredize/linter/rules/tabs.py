# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_bool
from tiredize.markdown.types.document import Document


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate document meets tab usage requirements.
    """
    results: list[RuleResult] = []
    text = document.string
    cursor = 0

    tabs_allowed = get_config_bool(config, "allowed")

    for line in text.splitlines(keepends=True):
        line_text = line
        if line.endswith("\n"):
            line_text = line[:-1]
            if line_text.endswith("\r"):
                line_text = line_text[:-1]

        if not tabs_allowed:
            split_line = line_text.split("\t")
            if len(split_line) > 1:
                offset_in_line = 0
                for segment in split_line[:-1]:
                    offset_in_line += len(segment)
                    position = Position(
                        offset=cursor + offset_in_line,
                        length=1,
                    )
                    results.append(
                        RuleResult(
                            message="Line contains a tab character.",
                            position=position,
                            rule_id=None,
                        )
                    )
                    offset_in_line += 1
        cursor += len(line)

    return results
