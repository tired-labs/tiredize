# Specification: CodeBlock

**GFM Equivalent:** Fenced code blocks (GFM spec section 4.5)
**Source File:** `tiredize/markdown/types/code.py`
**GFM Compliance:** Partial

## Description

A fenced code block is a sequence of lines enclosed by backtick fences.
The opening fence consists of three or more backticks followed by an
optional language identifier. The closing fence must use the same number
of backticks as the opening fence. Content between the fences is treated
as literal text and is never parsed for other markdown elements.

CodeBlock has the highest sanitization precedence — all other extractors
sanitize code blocks before matching to prevent false positives inside
fenced code.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `code` | `str` | The content between the opening and closing fences |
| `delimiter` | `str` | The opening fence string (e.g., ```` ``` ````) |
| `language` | `str` | The language identifier after the opening fence (may be empty) |
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text including fences |

## Regex Pattern

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<delimiter>``[`]+)   # Opening fence: 3+ backticks
(?P<language>.*)        # Optional language identifier
\n                      # Newline after opening fence
(?P<code>[\s\S]*?)      # Code content (lazy, spans newlines)
\n                      # Newline before closing fence
\1                      # Closing fence: must match opening backtick count
```

The closing fence uses backreference `\1` to ensure the delimiter
length matches. `[\s\S]*?` is used instead of `.*?` because `.`
does not match newlines. The lazy quantifier prevents consuming
past the first matching closing fence.

## Sanitization

**Chain (in order):** (none — highest precedence)
**Own sanitize():** Replaces entire match (fences + content) with
whitespace, preserving character offsets for downstream extractors.

## GFM Compliance

Partial compliance with GFM spec section 4.5. Known gaps:

- Tilde-fenced code blocks (`~~~` delimiter) not matched. Regex
  only handles backtick fences.
- Indented code fences (1-3 spaces before `` ``` ``) not matched.
  Start-of-line anchor requires no leading whitespace.
- Closing fence with trailing spaces not matched. Backreference
  `\1` requires exact delimiter match.
- Empty code block (zero content lines: `` ```\n``` ``) not
  matched. Pattern requires `\n` before closing fence but no
  content newline exists.
- CRLF line endings cause complete match failure. Pattern uses
  literal `\n`.

## Notes

- The `extract()` method has no sanitization chain — CodeBlock is
  the highest-precedence element type.
- The start-of-line anchor `(?:(?<=\n)|(?:^))` prevents matching
  inside table cells or other inline contexts. See the hub spec
  for anchor details.
