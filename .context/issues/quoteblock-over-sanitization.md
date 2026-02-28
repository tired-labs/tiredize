Status: draft
Parent: test-coverage-audit.md

# QuoteBlock Over-Sanitization

## Summary

QuoteBlock.sanitize() removes the entire content of blockquote lines,
including valid markdown elements (links, images, references) that
appear inside them. Per GFM, blockquotes are containers -- their
content is real markdown that should be parsed and extracted. The
current sanitization approach treats blockquotes as opaque regions
and blanks them entirely, causing downstream extractors that sanitize
QuoteBlock to miss valid elements.

Identified during the test coverage audit
(`test-coverage-markdown-types.md`). 3 skipped spec tests document
the bug.

## Findings

### Skipped spec tests (3)

1. **InlineLink inside quote block**
   `test_link.py::test_inline_link_inside_quote_block`
   `> [link](https://example.com)` -- the InlineLink is a valid
   link per GFM. InlineLink.extract() sanitizes QuoteBlock, which
   removes the entire `> [link](https://example.com)` text,
   preventing the InlineLink from being found.

2. **BracketLink inside quote block**
   `test_link.py::test_bracket_link_inside_quote_block`
   `> <https://example.com>` -- same issue. BracketLink sanitizes
   QuoteBlock, losing the valid bracket link.

3. **BareLink inside quote block**
   `test_link.py::test_bare_link_inside_quote_block`
   `> https://example.com` -- same issue. BareLink sanitizes
   QuoteBlock, losing the valid bare link.

### Correctly working cases (not affected)

- **InlineImage inside quote block**: InlineImage does NOT sanitize
  QuoteBlock, so `> ![alt](url)` IS correctly extracted. (However,
  InlineImage has its own sanitization gap -- it doesn't sanitize
  anything, tracked in `parser-sanitization-gaps.md`.)

- **LinkReference and ImageReference inside quote blocks**: These do
  NOT sanitize QuoteBlock, so `> [text][ref]` and `> ![alt][ref]`
  ARE correctly extracted.

- **ReferenceDefinition inside quote blocks**: The start-of-line
  anchor `(?<![^|\n])` prevents matching because `>` precedes `[`.
  This is correct -- GFM reference definitions inside blockquotes
  are scoped to the blockquote, not the document.

### Root cause

`QuoteBlock.sanitize()` uses `sanitize_text()` which replaces the
entire matched region with whitespace. The QuoteBlock regex
`(?<![^|\n])(?P<depth>[>]+)\s*(?P<quote>[^\n]*)` matches the full
blockquote line including its content. When this is replaced with
whitespace, all content is lost.

### Extractors that sanitize QuoteBlock

- InlineLink (line 133: `QuoteBlock.sanitize(text_sanitized)`)
- BracketLink (line 80)
- BareLink (line 30)

These three link types lose all content that appears inside
blockquotes.

## Acceptance Criteria

- [ ] Links inside blockquotes are correctly extracted by
      InlineLink, BracketLink, and BareLink
- [ ] All 3 skipped spec tests unskipped and passing
- [ ] QuoteBlock sanitization does not break extraction of other
      element types inside blockquotes
- [ ] No regressions in existing tests

## Out of Scope

- InlineImage sanitization chain (tracked in
  `parser-sanitization-gaps.md`)
- GFM syntax variant support (tracked in `gfm-parity.md`)
- sanitize_text utility bug (tracked in
  `sanitize-text-newline-bug.md`)

## Design Decisions

## Open Questions

- Should QuoteBlock.sanitize() only remove the `> ` prefix instead
  of the entire line content? This would preserve the content for
  downstream extractors while still preventing the `>` from
  interfering with other patterns.
- Should the link extractors stop sanitizing QuoteBlock entirely
  and instead strip the `> ` prefix before matching?
- How should multiline blockquotes interact with sanitization? If
  a link spans multiple `> ` lines, the `> ` prefix on each line
  would need to be stripped.
