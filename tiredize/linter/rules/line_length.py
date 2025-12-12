from __future__ import annotations
from tiredize.linter.types import RuleResult
from tiredize.linter.utils import get_config_int
# from tiredize.linter.utils import get_config_bool
# from tiredize.linter.utils import get_config_list
from tiredize.markdown.types.document import Document
from tiredize.types import Position
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
    # ignore_code_blocks = get_config_bool(config, "ignore_code_blocks")
    # ignore_frontmatter = get_config_bool(config, "ignore_frontmatter")
    # ignore_sections_list = get_config_list(config, "ignore_sections")

    results: typing.List[RuleResult] = []

    lines = document.string_markdown.splitlines()
    for line_number, line in enumerate(lines, start=1):
        line_length = len(line)
        if line_length <= maximum_length:
            continue

        overflow = line_length - maximum_length
        position = Position(
            line=line_number,
            offset=maximum_length,
            length=overflow,
        )

        results.append(
            RuleResult(
                message=(
                    f"Line {line_number} exceeds maximum length of "
                    f"{maximum_length} characters ({line_length} found)."
                ),
                position=position,
                rule_id=None
            )
        )

    return results
