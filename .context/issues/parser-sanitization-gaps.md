Status: completed
Parent: test-coverage-audit.md

# Parser Sanitization Gaps

## Summary

Several markdown extractors are missing sanitization calls in their
extraction chains, causing false positive matches when one element
type appears inside another. Identified during the test coverage audit
(`test-coverage-markdown-types.md`). 4 skipped spec tests document
the gaps, plus additional documented-behavior tests.

## Findings

### Skipped spec tests (4)

1. **InlineImage does not sanitize CodeBlock**
   `test_image.py::test_image_not_inside_code_block`
   `![alt](url)` inside a fenced code block is incorrectly extracted
   as an InlineImage. InlineImage has NO sanitization chain at all.

2. **InlineImage does not sanitize CodeInline**
   `test_image.py::test_image_not_inside_inline_code`
   `![alt](url)` inside backtick spans is incorrectly extracted.
   Same root cause: InlineImage has no sanitization.

3. **LinkReference does not sanitize CodeInline**
   `test_reference.py::test_link_reference_not_inside_inline_code`
   `[text][ref]` inside backtick spans is incorrectly extracted.
   LinkReference sanitizes CodeBlock but not CodeInline.

4. **ImageReference does not sanitize CodeInline**
   `test_reference.py::test_image_reference_not_inside_inline_code`
   `![alt][ref]` inside backtick spans is incorrectly extracted.
   ImageReference sanitizes CodeBlock but not CodeInline.

### Documented-behavior tests (not skipped)

5. **CodeInline does not sanitize CodeBlock**
   `test_codeblock.py::test_inline_code_inside_code_block`
   Backtick-delimited inline code inside fenced code blocks produces
   CodeInline false positives. CodeInline.extract() has no
   sanitization chain.

### Sanitization chain summary

Current sanitization chains per extractor:

| Extractor           | Sanitizes                                    |
|---------------------|----------------------------------------------|
| CodeBlock           | (none)                                       |
| CodeInline          | (none)                                       |
| Header              | CodeBlock                                    |
| InlineImage         | (none) **<-- gap**                           |
| InlineLink          | CodeBlock, CodeInline, QuoteBlock             |
| BracketLink         | CodeBlock, CodeInline, QuoteBlock             |
| BareLink            | CodeBlock, CodeInline, QuoteBlock,            |
|                     | InlineImage, BracketLink, InlineLink,         |
|                     | ReferenceDefinition                          |
| ReferenceDefinition | CodeBlock                                    |
| LinkReference       | CodeBlock                                    |
| ImageReference      | CodeBlock                                    |
| QuoteBlock          | CodeBlock                                    |
| Table               | (none, but Section._extract passes           |
|                     |  CodeBlock-sanitized text)                   |

### Missing sanitizations needed

- InlineImage: needs CodeBlock, CodeInline (minimum)
- CodeInline: needs CodeBlock
- LinkReference: needs CodeInline
- ImageReference: needs CodeInline

## Acceptance Criteria

- [x] InlineImage.extract() sanitizes CodeBlock and CodeInline
      before matching
- [x] CodeInline.extract() sanitizes CodeBlock before matching
- [x] LinkReference.extract() sanitizes CodeInline before matching
- [x] ImageReference.extract() sanitizes CodeInline before matching
- [x] All 4 skipped spec tests unskipped and passing
- [x] CodeInline-inside-CodeBlock test updated to assert no match
- [x] No regressions in existing tests

## Out of Scope

- QuoteBlock over-sanitization (tracked separately)
- GFM syntax variant support (tracked in `gfm-parity.md`)
- Regex pattern changes (tracked in `parser-greedy-regex.md`)
- sanitize_text utility bug (tracked in
  `sanitize-text-newline-bug.md`, now completed)

## Design Decisions

- **InlineImage does not sanitize QuoteBlock.** GitHub renders
  images inside blockquotes (`> ![alt](url)` displays the image),
  so images inside blockquotes are valid content that should be
  extracted. Adding QuoteBlock sanitization would replicate the
  over-sanitization bug tracked in `quoteblock-over-sanitization.md`.
  When that bug is fixed (stripping `> ` prefix instead of blanking
  content), QuoteBlock sanitization can be added to InlineImage if
  needed.

- **Sanitization chains are documented in the parser specification.**
  The chain determines extraction correctness and is a contract.
  Documenting it in the spec provides concrete reference material
  for unit tests and bug fixes, and helps future users of the tool
  understand the extraction logic.

- **Each extractor sanitizes internally, independent of calling
  context.** Extractors are designed as self-contained modules that
  produce correct results regardless of whether they are called from
  Section._extract(), standalone scripts, or a future API. Adding
  CodeBlock sanitization inside CodeInline.extract() is correct even
  though Section._extract() already creates a CodeBlock-sanitized
  copy — the internal sanitization makes the extractor safe in any
  context.

## Open Questions
