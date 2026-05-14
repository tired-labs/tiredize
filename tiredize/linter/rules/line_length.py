# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_int
from tiredize.linter.utils import get_config_list
from tiredize.markdown.types.document import Document


_ELEMENT_MAP = {
    "code_block": lambda s: s.code_block,
    "code_inline": lambda s: s.code_inline,
    "header": lambda s: [s.header] if s.header.position.length > 0 else [],
    "image_inline": lambda s: s.images_inline,
    "image_reference": lambda s: s.images_reference,
    "link_bare": lambda s: s.links_bare,
    "link_bracket": lambda s: s.links_bracket,
    "link_inline": lambda s: s.links_inline,
    "link_reference": lambda s: s.links_reference,
    "quoteblock": lambda s: s.quoteblocks,
    "reference_definition": lambda s: s.reference_definitions,
    "table": lambda s: s.tables,
}


def _build_excluded_ranges(
    document: Document,
    exclude: list[str],
) -> list[tuple[int, int]]:
    for name in exclude:
        if name not in _ELEMENT_MAP:
            raise ValueError(f"Unknown element name in exclude: '{name}'")

    ranges: list[tuple[int, int]] = []
    for section in document.sections:
        for name in exclude:
            for elem in _ELEMENT_MAP[name](section):
                start = elem.position.offset
                end = start + elem.position.length
                if end > start:
                    ranges.append((start, end))
    return ranges


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate document meets line length requirements.

    Configuration:
        maximum_length: int - The maximum allowed line length.
        exclude: list[str] - Element types whose lines are exempt from the limit.
    """
    maximum_length = get_config_int(config, "maximum_length")
    if maximum_length is None:
        return []

    exclude = get_config_list(config, "exclude") or []
    excluded_ranges = _build_excluded_ranges(document, exclude)

    results: list[RuleResult] = []
    text = document.string
    cursor = 0

    for line in text.splitlines(keepends=True):
        line_end = cursor + len(line)

        line_excluded = any(
            cursor < exc_end and line_end > exc_start
            for exc_start, exc_end in excluded_ranges
        )

        if not line_excluded:
            line_text = line
            if line.endswith("\n"):
                line_text = line[:-1]
                if line_text.endswith("\r"):
                    line_text = line_text[:-1]

            line_length = len(line_text)
            if line_length > maximum_length:
                overflow = line_length - maximum_length
                position = Position(
                    offset=cursor + maximum_length,
                    length=overflow,
                )
                results.append(
                    RuleResult(
                        message=(
                            f"Line exceeds maximum length of {maximum_length} "
                            f"({line_length} found)."
                        ),
                        position=position,
                        rule_id=None,
                    )
                )

        cursor += len(line)
    return results
