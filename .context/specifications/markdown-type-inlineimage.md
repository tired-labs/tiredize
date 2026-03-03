# Specification: InlineImage

**GFM Equivalent:** Images (GFM spec section 6.4)
**Source File:** `tiredize/markdown/types/image.py`
**GFM Compliance:** Partial

## Description

An inline image is written as `![alt text](url "optional title")`.
The parser extracts the alt text, URL, and optional title. Images
are distinguished from inline links by the leading `!` character.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | `str` | Alt text between `![` and `]` |
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text |
| `title` | `str \| None` | Optional title in double quotes, or None |
| `url` | `str` | The URL between `(` and `)` |

## Regex Pattern

```
!\[                           # Opening: exclamation mark + bracket
\s*                           # Optional whitespace
(?P<text>[^]]*?)              # Alt text (lazy, excludes ])
\s*                           # Optional whitespace
\]\(                          # Closing bracket + opening parenthesis
\s*                           # Optional whitespace
(?P<url>[^\s)]+)              # URL: non-whitespace, excludes )
(\s*?\"(?P<title>[^"]*?)\")?  # Optional title in double quotes
\s*\)                         # Closing parenthesis
```

The `[^\s)]+` URL pattern prevents greedy consumption past the
closing `)`. See the hub spec "URL Pattern in Inline Links and
Images" section.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets. Used by BareLink's sanitization
chain to prevent bare URL matching inside image syntax.

## GFM Compliance

Partial compliance with GFM spec section 6.4. Known gaps:

- Single-quote title (`![alt](url 'title')`) not captured.
  Regex only matches double-quoted titles.
- Angle-bracket URL (`![alt](<url with spaces>)`) not matched.
  `[^\s)]+` cannot handle spaces.
- `]` in alt text breaks match. `[^]]*?` stops at first `]`,
  no escape handling.
- Empty URL (`![alt]()`) not matched. `[^\s)]+` requires at
  least one character.
- Escaped quote in title (`"title \" here"`) truncated.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| InlineImage | Image |

The "Inline" prefix distinguishes this from ImageReference (which
uses reference-style syntax).

## Notes

- URLs containing literal `)` (e.g., balanced parentheses in
  Wikipedia URLs) are not supported. Tracked in `gfm-parity.md`.
