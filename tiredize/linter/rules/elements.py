# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import RuleResult
from tiredize.linter.utils import get_config_list
from tiredize.markdown.types.document import Document


_ELEMENT_LABELS = {
    "code_block": "Fenced code block",
    "code_inline": "Inline code",
    "header": "Header",
    "image_inline": "Inline image",
    "image_reference": "Reference-style image",
    "link_bare": "Bare link",
    "link_bracket": "Bracket link",
    "link_inline": "Inline link",
    "link_reference": "Reference-style link",
    "quoteblock": "Blockquote",
    "reference_definition": "Reference definition",
    "table": "Table",
}

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


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate that the document does not contain disallowed element types.

    Configuration:
        disallow: list[str] - Element types that must not appear in the document.
    """
    disallow = get_config_list(config, "disallow") or []
    if not disallow:
        return []

    for name in disallow:
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
