# Specification: FrontMatter

**GFM Equivalent:** Not in GFM spec
**Source File:** `tiredize/markdown/types/frontmatter.py`
**GFM Compliance:** N/A

## Description

YAML frontmatter is a block of YAML content delimited by `---` lines
at the very start of a document. It is not part of the GFM
specification but is widely supported by static site generators,
documentation tools, and GitHub itself (for rendering metadata).

FrontMatter is extracted before section parsing. The `Document._parse()`
method calls `FrontMatter.extract()` first, strips the frontmatter
from the text, and passes the remainder to `Section.extract()`.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `content` | `dict[Any, Any]` | Parsed YAML content (via `yaml.safe_load`) |
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text including `---` delimiters |

## Regex Pattern

```
^                       # Must be at absolute start of string
[-]{3}                  # Opening fence: ---
\n                      # Newline
(?P<yaml>[\s\S]*?)      # YAML content (lazy, spans newlines)
\n                      # Newline
[-]{3}                  # Closing fence: ---
\n                      # Trailing newline
```

Anchored to `^` (start of string), not start-of-line. FrontMatter
is always the first thing in a document. The closing `---\n` requires
a trailing newline, so `---` at end-of-file without a newline will
not match.

## Sanitization

**Chain (in order):** (none — extracted before Section parse)
**Own sanitize():** Replaces entire match with whitespace. Not used
by other extractors (frontmatter is stripped from the text before
section parsing begins).

## GFM Compliance

Not applicable. YAML frontmatter is not part of the GFM
specification. However, the implementation has known limitations
relative to common frontmatter conventions:

- `...` (three dots) closing delimiter not matched.
- Empty frontmatter (`---\n---\n`) not matched.
- More than 3 dashes (`----`) not matched. `[-]{3}` matches
  exactly 3.
- CRLF line endings cause complete match failure.

## Notes

- `extract()` returns `FrontMatter | None` (not a list) since a
  document can have at most one frontmatter block.
- If the YAML content fails to parse (`yaml.YAMLError`), `extract()`
  returns None — the frontmatter is silently skipped.
- FrontMatter is the only element type where `extract()` does not
  return a list.
