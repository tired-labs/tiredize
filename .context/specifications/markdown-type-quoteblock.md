# Specification: QuoteBlock

**GFM Equivalent:** Block quotes (GFM spec section 5.1)
**Source File:** `tiredize/markdown/types/quoteblock.py`
**GFM Compliance:** Partial

## Description

A block quote is one or more lines prefixed with `>` characters. The
regex matches individual lines; the `extract()` method merges
consecutive lines of the same depth into a single QuoteBlock element.
Multi-level nesting is indicated by the `depth` field (e.g., `>>`
has depth 2).

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `depth` | `int` | Nesting depth, derived from count of `>` characters |
| `position` | `Position` | Character offset and length relative to document root |
| `quote` | `str` | The quote content (after `>` and optional whitespace), newline-joined for merged lines |
| `string` | `str` | The full matched text including `>` prefix, newline-joined for merged lines |

## Regex Pattern

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<depth>[>]+)         # Blockquote depth: one or more >
\s*                     # Optional whitespace after >
(?P<quote>[^\n]*)       # Quote content: rest of line
```

Matches individual blockquote lines. The `extract()` method merges
consecutive lines by checking whether the text between two matches
is exactly `"\n"` (or `"\r\n"`) and whether the depth is the same.
Merged lines have their `quote` and `string` fields joined with
`\n`, and `position.length` is extended to cover all merged lines.

## Sanitization

**Chain (in order):** CodeBlock
**Own sanitize():** Replaces entire match (prefix + content) with
whitespace, preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 5.1. Known gaps:

- Lazy continuation (`> first\nsecond` as single quote) not matched.
  Only lines starting with `>` are captured.
- Spaced nested quotes (`> > nested`) parsed as depth 1. Pattern
  `[>]+` requires consecutive `>` without spaces.
- Indented block quote (`   > quote`) not matched. Start-of-line
  anchor requires `>` immediately after newline.

## Notes

- Link extractors do not sanitize QuoteBlock. Per GFM, blockquote
  content is real markdown — links inside blockquotes are valid and
  should be extracted. The `>` prefix does not interfere with any
  link regex pattern. See issue `quoteblock-over-sanitization.md`.
- The merge logic in `extract()` uses `prev_end_local` tracking to
  detect consecutive lines, distinguishing between adjacent quote
  lines (merge) and non-adjacent lines (new QuoteBlock).
