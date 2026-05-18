# Standard library
from __future__ import annotations

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
