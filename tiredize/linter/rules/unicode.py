# Standard library
from __future__ import annotations
import bisect
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.rules._elements import _ELEMENT_MAP
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import get_config_list
from tiredize.markdown.types.document import Document


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
    Validate document meets unicode usage requirements.

    Configuration:
        allowed: bool - When True, unicode is permitted; excluded elements
            are then the only places where it is flagged. When False,
            unicode is forbidden; excluded elements are the only places
            where it is permitted.
        exclude: list[str] - Element types that are treated opposite to
            the 'allowed' setting.
    """
    allowed = get_config_bool(config, "allowed")
    if allowed is None:
        return []

    exclude = get_config_list(config, "exclude") or []
    excluded_ranges = _build_excluded_ranges(document, exclude)
    exc_starts = [s for s, _ in excluded_ranges]

    results: list[RuleResult] = []
    for offset, char in enumerate(document.string):
        if ord(char) <= 127:
            continue

        idx = bisect.bisect_right(exc_starts, offset) - 1
        in_excluded = idx >= 0 and excluded_ranges[idx][1] > offset

        if allowed == in_excluded:
            results.append(RuleResult(
                message=(
                    f"Unicode character {char!r} "
                    f"(U+{ord(char):04X}) is not permitted here."
                ),
                position=Position(offset=offset, length=1),
                rule_id=None,
            ))

    return results
