# Standard library
from __future__ import annotations
import bisect
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.rules._elements import _ELEMENT_MAP
from tiredize.linter.utils import get_config_int
from tiredize.linter.utils import get_config_list
from tiredize.linter.utils import validate_config
from tiredize.markdown.types.document import Document


# Configuration keys this rule accepts, and the subset it requires.
# `maximum_length` is required because the rule measures nothing
# without it; `exclude` has a working default of "exclude nothing".
_RULE_ID = "line_length"
_ALLOWED_KEYS = {
    "exclude": "list",
    "maximum_length": "int",
}
_REQUIRED_KEYS = ("maximum_length",)


def _build_excluded_ranges(
    document: Document,
    exclude: list[str],
) -> list[tuple[int, int]]:
    for name in exclude:
        if not isinstance(name, str):
            raise ValueError(
                "exclude entries must be strings, got "
                f"{type(name).__name__!r}: {name!r}"
            )
        if name not in _ELEMENT_MAP:
            raise ValueError(f"Unknown element name in exclude: '{name}'")

    raw: list[tuple[int, int]] = []
    for section in document.sections:
        for name in exclude:
            for elem in _ELEMENT_MAP[name](section):
                start = elem.position.offset
                end = start + elem.position.length
                if end > start:
                    raw.append((start, end))

    if not raw:
        return []

    raw.sort()
    merged: list[tuple[int, int]] = [raw[0]]
    for start, end in raw[1:]:
        if start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate document meets line length requirements.

    Configuration:
        maximum_length: int - The maximum allowed line length.
            Required.
        exclude: list[str] - Element types whose lines are exempt from
            the limit. Optional; defaults to no exemptions.

    Raises:
        ValueError: the configuration names a key this rule does not
            accept, gives an accepted key a wrong-typed value, omits
            a required key, or names an unknown element in exclude.
    """
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)

    # validate_config has confirmed maximum_length is present and an
    # int, so the accessor cannot return None here.
    maximum_length = get_config_int(config, "maximum_length")

    exclude = get_config_list(config, "exclude") or []
    excluded_ranges = _build_excluded_ranges(document, exclude)
    exc_starts = [s for s, _ in excluded_ranges]

    results: list[RuleResult] = []
    text = document.string
    cursor = 0

    for line in text.splitlines(keepends=True):
        line_end = cursor + len(line)

        idx = bisect.bisect_right(exc_starts, cursor) - 1
        line_excluded = (
            idx >= 0 and excluded_ranges[idx][1] > cursor
        ) or (
            idx + 1 < len(excluded_ranges)
            and excluded_ranges[idx + 1][0] < line_end
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
