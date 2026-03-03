Status: active

# Remove Dead Code: get_position_from_match

## Summary

`get_position_from_match()` in `tiredize/markdown/utils.py` is unused
-- nothing in the codebase calls it. Discovered during the test
coverage audit. Should be removed to reduce maintenance surface.

## Acceptance Criteria

- [x] Confirm `get_position_from_match` has zero callers (grep across
      all source and test files)
- [x] Remove the function from `tiredize/markdown/utils.py`
- [x] Update `tiredize/markdown/utils.py` imports if any become unused
      (no imports became unused — `re` is still used by `search_all_re`)
- [x] Update markdown-parser.md specification to remove the function
      from the Utility Functions section
- [x] All tests pass after removal

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

## Design Decisions

## Open Questions
