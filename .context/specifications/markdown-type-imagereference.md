# Specification: ImageReference

**GFM Equivalent:** Reference images (GFM spec section 6.4)
**Source File:** `tiredize/markdown/types/reference.py`
**GFM Compliance:** Partial

## Description

An image reference uses a label to refer to a URL defined elsewhere
by a ReferenceDefinition. Two forms are supported:

- Full reference: `![alt text][label]`
- Shortcut reference: `![label]` (label doubles as alt text)

The collapsed form (`![alt][]`) is not correctly handled — see
GFM compliance gaps.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `reference` | `str` | The reference label used for lookup |
| `string` | `str` | The full matched text |
| `text` | `str \| None` | Alt text (None for shortcut references) |

## Regex Pattern

```
!\[                     # Opening: exclamation mark + bracket
(\s*(?P<text>[^]]*?)    # Optional: alt text (lazy, excludes ])
\s*\]\[)?               # Optional: closing bracket + opening bracket
\s*                     # Optional whitespace
(?P<reference>[^\]]+)   # Reference label (excludes ])
\s*                     # Optional whitespace
\](?!:)                 # Closing bracket, not followed by :
(?!\()                  # Not followed by ( (excludes inline images)
```

Same structure as LinkReference but anchored by `![` instead of
lookbehind filtering. Matches both full `![alt][ref]` and shortcut
`![ref]` forms.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 6.4. Known gaps:

- Collapsed image reference (`![alt][]`) same issue as
  LinkReference — detected as shortcut reference.
- `]` in reference label breaks match. `[^\]]+` stops at
  first `]`.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| ImageReference | Reference image |

## Notes

- Defined in the same source file as ReferenceDefinition and
  LinkReference (`reference.py`).
