from __future__ import annotations
from tiredize.linter.types import RuleResult
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import get_config_dict
from tiredize.markdown.types.document import Document
from tiredize.types import Position
import typing


def validate(
    document: Document,
    config: typing.Dict[str, typing.Any],
) -> typing.List[RuleResult]:
    """
    Validate document meets whitespace requirements.

    Configuration:
        maximum_length: int - The maximum allowed line length.
    """
    tabs_dict = get_config_dict(config, "tabs")
    trailing_whitespace_dict = get_config_dict(config, "trailing_whitespace")
    if (tabs_dict is None) and (trailing_whitespace_dict is None):
        return []

    results: typing.List[RuleResult] = []
    lines = document.string_markdown.splitlines()

    tabs_allowed = True
    if tabs_dict is not None:
        tabs_allowed = get_config_bool(
            tabs_dict,
            "allowed"
        )

    trailing_whitespace_allowed = True
    if trailing_whitespace_dict is not None:
        trailing_whitespace_allowed = get_config_bool(
            trailing_whitespace_dict,
            "allowed"
        )

    for line_number, line in enumerate(lines, start=1):
        if not tabs_allowed:
            split_line = line.split("\t")
            if len(split_line) > 1:
                offset = 0
                for segment in split_line[:-1]:
                    offset += len(segment)
                    position = Position(
                        line=line_number,
                        offset=offset,
                        length=1,
                    )
                    results.append(
                        RuleResult(
                            message=(
                                f"Line {line_number} contains a tab character."
                            ),
                            position=position,
                            rule_id=None
                        )
                    )
                    offset += 1

        if not trailing_whitespace_allowed:
            stripped_line = line.rstrip()
            if len(stripped_line) < len(line):
                offset = len(stripped_line)
                length = len(line) - len(stripped_line)
                position = Position(
                    line=line_number,
                    offset=offset,
                    length=length,
                )
                results.append(
                    RuleResult(
                        message=(
                            f"Line {line_number} contains trailing "
                            f"whitespace."
                        ),
                        position=position,
                        rule_id=None
                    )
                )

    return results
