# Specification: InlineLink

**GFM Equivalent:** Links (GFM spec section 6.3)
**Source File:** `tiredize/markdown/types/link.py`
**GFM Compliance:** Partial

## Description

An inline link is written as `[text](url "optional title")`. The
parser extracts the link text, URL, and optional title. A negative
lookbehind prevents matching image syntax (`![text](url)`).

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text |
| `title` | `str` | Optional title in double quotes (None if absent) |
| `url` | `str` | The URL between `(` and `)` |

## Regex Pattern

```
(?<!!)                        # Negative lookbehind: not preceded by !
\[\s*                         # Opening bracket + optional whitespace
(?P<text>[^]]*?)              # Link text (lazy, excludes ])
\s*                           # Optional whitespace
\]\(                          # Closing bracket + opening parenthesis
\s*                           # Optional whitespace
(?P<url>[^\s)]+)              # URL: non-whitespace, excludes )
(\s*?\"(?P<title>[^"]*?)\")?  # Optional title in double quotes
\s*\)                         # Closing parenthesis
```

The `(?<!!)` lookbehind prevents matching `![text](url)` as a link
(images start with `!`). Otherwise identical to InlineImage's
pattern.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets. Used by BareLink's sanitization
chain.

## GFM Compliance

Partial compliance with GFM spec section 6.3. Known gaps:

- Single-quote title (`[t](url 'title')`) not captured. Regex
  only matches double-quoted titles.
- Parenthesis title (`[t](url (title))`) not captured.
- Angle-bracket URL (`[t](<url with spaces>)`) not matched.
  `[^\s)]+` cannot handle spaces.
- Empty URL (`[text]()`) not matched. `[^\s)]+` requires at least
  one character.
- Escaped brackets in link text (`[text \] here](url)`) broken.
  `[^]]*?` stops at first `]`, no escape handling.
- Nested brackets in link text (`[text [nested]](url)`) broken.
  Same `[^]]` issue.
- Escaped quote in title (`"title \" here"`) truncated.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| InlineLink | Link (inline variant) |

The "Inline" prefix distinguishes this from LinkReference (which
uses reference-style syntax).

## Notes

- The `text` field is captured as a named group in the regex but
  is not exposed as a dataclass field. The InlineLink dataclass
  has `title` (from the optional quoted title) and `url`, but
  the link display text captured by `(?P<text>...)` is only
  accessible via the `string` field.
- URLs containing literal `)` are not supported. Tracked in
  `gfm-parity.md`.
