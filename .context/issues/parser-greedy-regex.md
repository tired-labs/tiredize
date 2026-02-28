Status: draft
Parent: test-coverage-audit.md

# Parser Greedy Regex Bugs

## Summary

Several regex patterns in the markdown parser match too much or
produce incorrect boundaries, causing wrong data to be captured or
false positive matches. These are distinct from GFM parity issues
(missing syntax support) -- the parser attempts to match but produces
wrong results.

Identified during the test coverage audit
(`test-coverage-markdown-types.md`). 1 skipped spec test plus several
documented-behavior tests capture the findings.

## Findings

### Skipped spec test (1)

1. **InlineImage greedy URL**
   `test_image.py::test_image_adjacent_to_link`
   `![img](a.png)[link](b.html)` -- the URL regex `\S+` in
   InlineImage consumes past the closing `)` into the adjacent link
   syntax. URL becomes `a.png)[link](b.html` instead of `a.png`.

   Root cause: `(?P<url>\S+)` matches any non-whitespace greedily.
   The `)` closing the image is consumed as part of the URL because
   `\S` matches `)`. The regex backtracks to find `\s*\)` at the
   end of the adjacent link instead.

   Same pattern exists in InlineLink (`RE_LINK_INLINE`) but is less
   likely to trigger because InlineLink has a negative lookbehind
   for `!` that prevents matching after `![`.

### Documented-behavior tests (not skipped)

2. **Table over-greedy row matching**
   `test_table.py::test_table_over_greedy_row_matching`
   The rows pattern `([^\n]+(\n|$))*` consumes ALL non-empty lines
   after the divider, including non-table content that follows the
   table. A line like `"This is not a table row."` is captured as
   a data row because it matches `[^\n]+`.

   Impact: Table.string includes text beyond the actual table,
   and Table.rows contains non-table lines.

3. **Pipe as start-of-line false positives**
   `test_codeblock.py::test_codeblock_after_pipe_char`
   `test_header.py::test_header_after_pipe_char`
   `test_quoteblock.py::test_quoteblock_after_pipe_char`
   `test_reference.py::test_reference_definition_after_pipe_char`

   The `(?<![^|\n])` anchor used in CodeBlock, Header, QuoteBlock,
   and ReferenceDefinition treats `|` as a valid start-of-line
   character. Content after `|` (e.g., inside table cells) can
   trigger false positive matches for these element types.

   This may be intentional design -- the `|` exception might exist
   so these elements can be detected inside table cells. But it
   also means `|# Heading`, `|> Quote`, `|\`\`\`` are matched as
   if they were real elements.

4. **BareLink `../` partial match**
   `test_link.py::test_bare_link_parent_dir_not_partial_match`
   (skipped under gfm-parity, but root cause is greedy regex)
   The BareLink regex `(\.\/|\\)` matches `./` inside `../`,
   starting at position 1. `../sibling/readme.md` becomes
   `./sibling/readme.md` starting at the wrong position.

5. **ImageReference dead lookbehind**
   `test_reference.py::test_image_reference_dead_lookbehind`
   The lookbehind `(?<!(\]))` in ImageReference checks whether `!`
   (the preceding literal in the pattern) is `]`. Since `!` is
   never `]`, the lookbehind always passes and provides no
   filtering. This is dead code, not a false positive, but it
   suggests the regex was intended to prevent matching after `]`
   but was implemented incorrectly.

## Acceptance Criteria

- [ ] InlineImage URL regex does not consume past closing `)`
- [ ] Table rows pattern stops at first non-table line (e.g.,
      line not containing `|` or empty line)
- [ ] Pipe-as-start-of-line behavior evaluated: intentional design
      decision or bug to fix
- [ ] BareLink regex does not partial-match `../` paths
- [ ] ImageReference lookbehind fixed or removed
- [ ] All affected skipped spec tests unskipped and passing
- [ ] No regressions in existing tests

## Out of Scope

- GFM syntax variant support (tracked in `gfm-parity.md`)
- Missing sanitization chains (tracked in
  `parser-sanitization-gaps.md`)
- sanitize_text utility bug (tracked in
  `sanitize-text-newline-bug.md`)

## Design Decisions

## Open Questions

- Is the `|` in `(?<![^|\n])` an intentional design choice for
  table cell processing? If so, should it be documented rather
  than fixed?
- Should InlineImage and InlineLink URL patterns use `[^\s)]+`
  instead of `\S+` to stop at `)` boundaries?
- Should Table row matching require `|` in each line, or use a
  blank-line terminator?
