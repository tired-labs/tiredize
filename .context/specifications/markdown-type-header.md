# Specification: Header

**GFM Equivalent:** ATX headings (GFM spec section 4.2)
**Source File:** `tiredize/markdown/types/header.py`
**GFM Compliance:** Partial

## Description

An ATX heading is a line beginning with 1-6 `#` characters followed
by mandatory whitespace and a title. The number of `#` characters
determines the heading level. Headers are used by `Section.extract()`
to split documents into sections — each header starts a new section.

The `slugify_header()` static method generates GitHub-compatible
anchor slugs for headings, handling duplicate titles by appending
numeric suffixes.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `level` | `int` | Heading level (1-6), derived from hash count |
| `position` | `Position` | Character offset and length relative to document root |
| `slug` | `str` | GitHub-style anchor slug (e.g., `#my-heading`) |
| `string` | `str` | The full matched text including hashes |
| `title` | `str` | The heading text after the hashes and whitespace |

## Regex Pattern

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<hashes>\#{1,6})     # 1-6 hash characters (heading level)
\s+                     # Mandatory whitespace after hashes
(?P<title>[^\n]+)       # Title: rest of line
```

Requires at least one space after `#`. A line like `#no-space` will
not match. The title captures everything to end-of-line including
trailing whitespace and closing `#` characters.

## Sanitization

**Chain (in order):** CodeBlock
**Own sanitize():** Replaces entire match (hashes + whitespace +
title) with whitespace, preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 4.2. Known gaps:

- Closing hashes (`# Heading ##`) not stripped from title. `[^\n]+`
  captures trailing `#` characters as part of title text.
- Empty heading (`# ` with only whitespace after hash) not matched.
  `[^\n]+` requires at least one content character after `\s+`
  consumes the space.
- Leading spaces (1-3 before `#`: `   # Heading`) not matched.
  Start-of-line anchor requires `#` immediately after newline.
- Setext headings (`Heading\n=======` and `Heading\n-------`) not
  supported. Parser only handles ATX-style.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| Header | ATX heading |

## Notes

- `slugify_header()` follows the GitHub slug algorithm: lowercase,
  strip punctuation (keep hyphens and spaces), spaces to hyphens,
  collapse consecutive hyphens, strip leading/trailing hyphens,
  prepend `#`. Duplicate titles get `-1`, `-2`, etc. suffixes.
- `slugify_header()` currently strips non-ASCII characters. See
  issue `fix-slug-non-ascii.md`.
- `extract()` is called by both `Section.extract()` (for section
  splitting) and `Section._extract()` (for per-section header
  extraction). The `Section.extract()` call operates on full
  document text; `Section._extract()` operates on section slices.
