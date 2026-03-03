# Specification: Section

**GFM Equivalent:** Not in GFM spec (structural container)
**Source File:** `tiredize/markdown/types/section.py`
**GFM Compliance:** N/A

## Description

Section is the primary organizational unit of a parsed document.
Each section corresponds to a heading and the content that follows
it until the next heading of equal or higher level. Section serves
two roles:

1. **Tree builder:** `Section.extract()` splits document text into
   sections by heading positions and establishes parent-child
   relationships via `_map_subsections()`.
2. **Extraction orchestrator:** `Section._extract()` calls every
   element type's `extract()` method on the section's text,
   populating all element lists.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `code_block` | `list[CodeBlock]` | Fenced code blocks in this section |
| `code_inline` | `list[CodeInline]` | Inline code spans in this section |
| `header` | `Header` | The section's heading (level-0 synthetic header if no heading) |
| `images_inline` | `list[InlineImage]` | Inline images in this section |
| `images_reference` | `list[ImageReference]` | Image references in this section |
| `links_bare` | `list[BareLink]` | Bare links in this section |
| `links_bracket` | `list[BracketLink]` | Bracket links (autolinks) in this section |
| `links_inline` | `list[InlineLink]` | Inline links in this section |
| `links_reference` | `list[LinkReference]` | Link references in this section |
| `lists` | `list[List]` | Lists in this section (always empty — List is a stub) |
| `position` | `Position` | Character offset and length relative to document root |
| `quoteblocks` | `list[QuoteBlock]` | Block quotes in this section |
| `reference_definitions` | `list[ReferenceDefinition]` | Reference definitions in this section |
| `string` | `str` | The raw text of this section |
| `string_safe` | `str` | Section text with CodeBlock and CodeInline sanitized |
| `subsections` | `list[Section]` | Child sections (lower-level headings) |
| `tables` | `list[Table]` | Tables in this section |

## Regex Pattern

None. Section is a structural container, not a pattern-matched
element.

## Sanitization

Not applicable in the chain sense. Section itself is not sanitized
by other extractors. However:

- `_extract()` passes raw `string` to all extractors, relying on
  each to sanitize internally.
- The `string_safe` field is computed as
  `CodeInline.sanitize(CodeBlock.sanitize(string))`. It is not
  passed to any extractor — it is stored for downstream consumers
  (e.g., linter rules that need code-free text).

## GFM Compliance

Not applicable. Section is a structural concept specific to
tiredize's document model. GFM does not define sections.

## Notes

- `extract()` (public static method):
  1. Extracts all headers from the full text.
  2. If no headers are found, wraps the entire text in a single
     section with a synthetic level-0 header.
  3. Otherwise, splits text at header boundaries and creates one
     section per header.
  4. Calls `_map_subsections()` to establish parent-child
     relationships based on heading level.

- `_extract()` (private static method):
  1. Extracts the first header from the section text (or creates
     a synthetic level-0 header).
  2. Calls `extract()` on every element type, passing the section
     text and `base_offset`.
  3. Computes `string_safe`.
  4. Returns the populated Section.

- `_map_subsections()`:
  Maps subsection relationships. A section at level N contains
  subsections at level N+1 and deeper (until a section at level
  <= N is encountered). Level-0 headers (synthetic) never have
  subsections. The `header.level == 0` break in the loop is
  unreachable in practice because level-0 headers only appear
  when there are no real headers, which means there is only one
  section.
