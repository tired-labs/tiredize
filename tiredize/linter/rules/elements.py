# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import RuleResult
from tiredize.linter.rules._elements import _ELEMENT_LABELS
from tiredize.linter.rules._elements import _ELEMENT_MAP
from tiredize.linter.utils import get_config_list
from tiredize.linter.utils import validate_config
from tiredize.markdown.types.document import Document


# Configuration keys this rule accepts, and the subset it requires.
# `disallow` is required because the rule inspects nothing without
# it: enabling `elements` with no `disallow` would be a no-op.
_RULE_ID = "elements"
_ALLOWED_KEYS = {
    "disallow": "list",
}
_REQUIRED_KEYS = ("disallow",)


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate that the document does not contain disallowed element types.

    Configuration:
        disallow: list[str] - Element types that must not appear in the
            document. Required; an empty list allows everything.

    Raises:
        ValueError: the configuration names a key this rule does not
            accept, gives an accepted key a wrong-typed value, omits
            a required key, or names an unknown element in disallow.
    """
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)

    # validate_config has confirmed disallow is present and a list.
    disallow = get_config_list(config, "disallow")
    if not disallow:
        return []

    for name in disallow:
        if not isinstance(name, str):
            raise ValueError(
                "disallow entries must be strings, got "
                f"{type(name).__name__!r}: {name!r}"
            )
        if name not in _ELEMENT_MAP:
            raise ValueError(f"Unknown element name in disallow: '{name}'")

    results: list[RuleResult] = []
    for section in document.sections:
        for name in disallow:
            label = _ELEMENT_LABELS[name]
            for elem in _ELEMENT_MAP[name](section):
                if elem.position.length == 0:
                    continue
                results.append(
                    RuleResult(
                        message=f"{label} is not allowed.",
                        position=elem.position,
                        rule_id=None,
                    )
                )

    return results
