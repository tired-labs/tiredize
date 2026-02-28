Status: active
Parent: test-coverage-audit.md

# Test Coverage: Markdown Utils

## Summary

Write direct tests for `tiredize/markdown/utils.py` functions. Currently
covered only indirectly through element type extractors. Part of the
test coverage audit (`test-coverage-audit.md`).

## Acceptance Criteria

- [x] `tests/markdown/test_utils.py` -- direct tests for
      `search_all_re` covering: basic pattern match, multiple matches,
      no matches, empty string, re.VERBOSE syntax with comments
- [x] `tests/markdown/test_utils.py` -- direct tests for
      `sanitize_text` covering: single match replaced with whitespace,
      multiple matches, no matches, empty string, verify string length
      is preserved after sanitization
### Boundary and degenerate inputs (audit point 6)

- [x] `search_all_re` with single-character input, input that is
      entirely one match, input with overlapping potential matches
- [x] `sanitize_text` with input where the entire string matches the
      pattern, input with adjacent back-to-back matches

### Idempotency (audit point 7)

- [x] `sanitize_text` called twice with the same pattern and text --
      verify result is identical to a single call and string length is
      still preserved

### Unicode and non-ASCII (audit point 9)

- [x] `search_all_re` with pattern matching non-ASCII content (emoji,
      accented characters) -- verify match positions are correct
- [x] `sanitize_text` replacing a match containing multi-byte
      characters -- verify length is preserved in characters (Python
      str length), not bytes

### Coverage target

- [x] 100% coverage on `tiredize/markdown/utils.py`, excluding
      `get_position_from_match` (dead code, tracked by
      `dead-code-cleanup.md`)

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- `get_position_from_match()` -- dead code, tracked separately
- Element type extractors (covered by `test-coverage-markdown-types.md`)

## Design Decisions

## Open Questions
