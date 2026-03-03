# Specification: Document

**GFM Equivalent:** Not in GFM spec (structural container)
**Source File:** `tiredize/markdown/types/document.py`
**GFM Compliance:** N/A

## Description

Document is the top-level container for a parsed markdown file. It
orchestrates the full parse pipeline: extract frontmatter, strip it
from the text, extract sections from the remaining markdown, and
re-compute header slugs for document-wide uniqueness.

Document is the entry point for all parsing. External code calls
`Document.load()` with either a file path or raw text, and receives
a fully populated document tree.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `frontmatter` | `FrontMatter \| None` | Parsed YAML frontmatter, or None |
| `path` | `Path \| None` | File path if loaded from file, or None |
| `sections` | `list[Section]` | Top-level sections (each may have subsections) |
| `string_markdown` | `str` | Document text with frontmatter stripped |
| `string` | `str` | Full original document text |

Private fields:
| Field | Type | Description |
|-------|------|-------------|
| `_line_starts` | `list[int]` | Precomputed line-start offsets for `line_col()` |

## Regex Pattern

None. Document is a structural container, not a pattern-matched
element.

## Sanitization

Not applicable. Document does not participate in the sanitization
chain.

## GFM Compliance

Not applicable. Document is a structural concept with no GFM
equivalent. It is the parse orchestrator, not a rendered element.

## Notes

- `load()` accepts either `path` or `text`, not both. Raises
  `ValueError` if both are provided or neither is provided. Raises
  `FileNotFoundError` if the path does not exist.
- `_parse()` is called by `load()`. It:
  1. Extracts frontmatter via `FrontMatter.extract()`.
  2. Strips frontmatter from text to produce `string_markdown`.
  3. Computes `base_offset` (length of frontmatter + 1 newline).
  4. Calls `Section.extract()` on the markdown text.
  5. Re-computes header slugs across all sections for
     document-wide uniqueness using `slugify_header()`.
  6. Builds the line index for `line_col()`.
- `line_col(offset)` converts a character offset to
  `(line_number, column)` where line is 1-based and column is
  0-based. Uses `bisect.bisect_right` on precomputed line starts.
  Clamps out-of-range offsets to document boundaries.
