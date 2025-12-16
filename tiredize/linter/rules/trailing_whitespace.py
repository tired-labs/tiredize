from __future__ import annotations
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_bool
from tiredize.markdown.types.document import Document
import typing


def validate(
    document: Document,
    config: typing.Dict[str, typing.Any],
) -> typing.List[RuleResult]:
    """
    Validate document meets trailing whitespace requirements.
    """
    results: typing.List[RuleResult] = []
    text = document.string
    cursor = 0

    trailing_whitespace_allowed = get_config_bool(config, "allowed")

    for line in text.splitlines(keepends=True):
        line_text = line
        if line.endswith("\n"):
            line_text = line[:-1]
            if line_text.endswith("\r"):
                line_text = line_text[:-1]

        if not trailing_whitespace_allowed:
            stripped_line = line_text.rstrip()
            offset_in_line = 0
            if len(stripped_line) < len(line_text):
                offset_in_line += len(stripped_line)
                length = len(line_text) - len(stripped_line)
                position = Position(
                    offset=cursor + offset_in_line,
                    length=length
                )
                results.append(
                    RuleResult(
                        message="Line contains trailing whitespace.",
                        position=position,
                        rule_id=None
                    )
                )
        cursor += len(line)
    return results
