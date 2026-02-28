Status: draft
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

- [ ] InlineImage.extract() sanitizes CodeBlock and CodeInline
      before matching
- [ ] CodeInline.extract() sanitizes CodeBlock before matching
- [ ] LinkReference.extract() sanitizes CodeInline before matching
- [ ] ImageReference.extract() sanitizes CodeInline before matching
- [ ] All 4 skipped spec tests unskipped and passing
- [ ] CodeInline-inside-CodeBlock test updated to assert no match
- [ ] No regressions in existing tests

## Out of Scope

- QuoteBlock over-sanitization (tracked separately)
- GFM syntax variant support (tracked in `gfm-parity.md`)
- Regex pattern changes (tracked in `parser-greedy-regex.md`)
- sanitize_text utility bug (tracked in
  `sanitize-text-newline-bug.md`)

## Design Decisions

## Open Questions

- Should InlineImage also sanitize QuoteBlock (matching InlineLink's
  chain)?
- Should the sanitization chain for each extractor be documented in
  the parser specification?
- Does adding sanitization to CodeInline.extract() affect
  Section._extract() which already passes CodeBlock-sanitized text
  to CodeInline?
