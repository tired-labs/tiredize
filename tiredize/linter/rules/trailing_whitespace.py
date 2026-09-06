# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import validate_config
from tiredize.markdown.types.document import Document


# Configuration keys this rule accepts, and the subset it requires.
# `allowed` is optional: with the key absent the rule still forbids
# trailing whitespace, so enabling the rule is never a no-op.
_RULE_ID = "trailing_whitespace"
_ALLOWED_KEYS = {
    "allowed": "bool",
}
_REQUIRED_KEYS: tuple[str, ...] = ()


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate document meets trailing whitespace requirements.

    Configuration:
        allowed: bool - When True, trailing whitespace is permitted.
            Optional; it is forbidden when the key is absent.

    Raises:
        ValueError: the configuration names a key this rule does not
            accept, or gives an accepted key a wrong-typed value.
    """
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)

    results: list[RuleResult] = []
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
