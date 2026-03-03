# Specification: CodeInline

**GFM Equivalent:** Code spans (GFM spec section 6.1)
**Source File:** `tiredize/markdown/types/code.py`
**GFM Compliance:** Partial

## Description

An inline code span is a run of text enclosed by single backtick
characters on the same line. Content inside backticks is treated as
literal text and is never parsed for other markdown elements.

CodeInline has the second-highest sanitization precedence after
CodeBlock.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | The content between the backticks |
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text including backticks |

## Regex Pattern

```
`                       # Opening backtick
(?P<code>[^\n`]+)       # Content: any chars except backtick or newline
`                       # Closing backtick
```

The `[^\n`]` exclusion prevents matching across lines. Content must
be at least one character long (empty inline code `` ` ` `` will not
match).

## Sanitization

**Chain (in order):** CodeBlock
**Own sanitize():** Replaces entire match (backticks + content) with
whitespace, preserving character offsets for downstream extractors.

## GFM Compliance

Partial compliance with GFM spec section 6.1. Known gaps:

- Double-backtick inline code (`` `` code `` ``) not matched.
  Pattern only handles single-backtick delimiters.
- Triple-backtick inline code not matched. Same issue.
- Inline code containing a single backtick (multi-backtick wrapper)
  not supported. Would require matching balanced multi-backtick
  delimiters.
- Multiline inline code (`` `foo\nbar` ``) not matched. Character
  class `[^\n`]` excludes newlines.

## Notes

- Defined in the same source file as CodeBlock (`code.py`).
