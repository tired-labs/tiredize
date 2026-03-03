Status: completed
Parent: test-coverage-audit.md

# QuoteBlock Over-Sanitization

## Summary

InlineLink, BracketLink, and BareLink extractors sanitize QuoteBlock
before matching. QuoteBlock.sanitize() blanks the entire line
including content, which causes these extractors to miss valid links
inside blockquotes. Per GFM, blockquote content is real markdown —
links inside `> ` prefixed lines are rendered and should be extracted.

The `>` prefix does not actually interfere with any of the three link
regexes (verified empirically — none use start-of-line anchors or
characters that conflict with `>`). The QuoteBlock sanitization step
is unnecessary and should be removed from these extractors.

`QuoteBlock.sanitize()` itself is correct and unchanged — it blanks
entire blockquote lines, which is the right behavior for its own
contract.

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
  QuoteBlock, so `> ![alt](url)` IS correctly extracted.

- **LinkReference and ImageReference inside quote blocks**: These do
  NOT sanitize QuoteBlock, so `> [text][ref]` and `> ![alt][ref]`
  ARE correctly extracted.

- **ReferenceDefinition inside quote blocks**: The start-of-line
  anchor `(?:(?<=\n)|(?:^))` prevents matching because `>` precedes
  `[`.
  This is correct -- GFM reference definitions inside blockquotes
  are scoped to the blockquote, not the document.

### Root cause

The `>` prefix does not interfere with InlineLink, BracketLink, or
BareLink regex patterns. None of these regexes use start-of-line
anchors or characters that conflict with `>`. QuoteBlock sanitization
was added as a precaution but is unnecessary for these extractors.
Removing it from their sanitization chains allows links inside
blockquotes to be found correctly.

### Extractors that sanitized QuoteBlock (removed by this fix)

- InlineLink
- BracketLink
- BareLink

## Acceptance Criteria

- [x] `QuoteBlock.sanitize()` call removed from InlineLink.extract()
- [x] `QuoteBlock.sanitize()` call removed from BracketLink.extract()
- [x] `QuoteBlock.sanitize()` call removed from BareLink.extract()
- [x] QuoteBlock import removed from `link.py` if no longer used
- [x] All 3 skipped spec tests unskipped and passing
- [x] No regressions in existing tests
- [x] Parser specification updated: sanitization chain table updated
      to remove QuoteBlock from InlineLink, BracketLink, and BareLink
      chains
- [x] Parser specification known gaps section updated to remove the
      QuoteBlock over-sanitization note

## Out of Scope

- Changes to `QuoteBlock.sanitize()` itself (it works as intended)
- QuoteBlock as a container type with child elements (tracked in
  `container-element-model.md`)
- InlineImage sanitization chain (tracked in
  `parser-sanitization-gaps.md`)
- GFM syntax variant support (tracked in `gfm-parity.md`)

## Design Decisions

- **Remove QuoteBlock from link sanitization chains rather than
  modifying QuoteBlock.sanitize().** The `>` prefix does not
  interfere with link regexes, so sanitization is unnecessary.
  QuoteBlock.sanitize() correctly blanks entire lines and its
  contract should not change.

## Open Questions
