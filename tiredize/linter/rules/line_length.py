from __future__ import annotations
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_int
from tiredize.markdown.types.document import Document
import typing


def validate(
    document: Document,
    config: typing.Dict[str, typing.Any],
) -> typing.List[RuleResult]:
    """
    Validate document meets line length requirements.

    Configuration:
        maximum_length: int - The maximum allowed line length.
    """
    maximum_length = get_config_int(config, "maximum_length")
    if maximum_length is None:
        return []

    results: typing.List[RuleResult] = []

    text = document.string
    cursor = 0

    for line in text.splitlines(keepends=True):

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
