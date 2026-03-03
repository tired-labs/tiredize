# Specification: LinkReference

**GFM Equivalent:** Reference links — full and shortcut
(GFM spec section 6.3)
**Source File:** `tiredize/markdown/types/reference.py`
**GFM Compliance:** Partial

## Description

A link reference uses a label to refer to a URL defined elsewhere
by a ReferenceDefinition. Two forms are supported:

- Full reference: `[display text][label]`
- Shortcut reference: `[label]` (label doubles as display text)

The collapsed form (`[text][]`) is not correctly handled — see
GFM compliance gaps.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `reference` | `str` | The reference label used for lookup |
| `string` | `str` | The full matched text |
| `text` | `str \| None` | Display text (None for shortcut references) |

## Regex Pattern

```
(?<!(!|\]))\[           # Not preceded by ! or ] + opening bracket
(\s*(?P<text>[^]]*?)    # Optional: link text (lazy, excludes ])
\s*\]\[)?               # Optional: closing bracket + opening bracket
\s*                     # Optional whitespace
(?P<reference>[^\]]+)   # Reference label (excludes ])
\s*                     # Optional whitespace
\](?!:)                 # Closing bracket, not followed by :
(?!\()                  # Not followed by ( (excludes inline links)
```

Matches both full references `[text][ref]` and shortcut references
`[ref]`. The `(?<!(!|\]))` lookbehind prevents matching image
references (`![alt][ref]`) and consecutive bracket sequences. The
`(?!:)` lookahead prevents matching reference definitions
`[ref]:`. The `(?!\()` lookahead prevents matching inline links
`[text](url)`.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 6.3. Known gaps:

- Collapsed reference (`[text][]`) detected as shortcut reference
  instead. `text` field is None instead of content.
- `]` in reference label breaks match. `[^\]]+` stops at first `]`.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| LinkReference | Full reference link / Shortcut reference link |

## Notes

- Defined in the same source file as ReferenceDefinition and
  ImageReference (`reference.py`).
