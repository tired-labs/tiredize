Status: draft

# Fix slugify_header to preserve non-ASCII characters

## Summary

`slugify_header()` in `tiredize/markdown/types/header.py` uses
`re.sub(r"[^a-z0-9 \-]", "", slug)` which strips all non-ASCII
characters. A heading like "Café Section" produces `#caf-section`
instead of the GFM-correct `#café-section`. This breaks anchor
links for any heading containing accented characters, CJK text,
or other non-ASCII letters.

Discovered during the test coverage audit
(`test-coverage-linter-utils-engine.md`). A spec-correct test exists
and is currently skipped:
`tests/linter/test_utils.py::test_anchor_with_non_ascii_slug`.

## Acceptance Criteria

- [ ] `slugify_header` preserves non-ASCII letters (accented, CJK,
      etc.) while still removing punctuation
- [ ] "Café Section" produces `#café-section`, not `#caf-section`
- [ ] The skipped test `test_anchor_with_non_ascii_slug` is unskipped
      and passes
- [ ] All existing tests pass (no regressions)
- [ ] Markdown parser specification updated to document slug
      generation rules including non-ASCII handling

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Full GFM parity (tracked in `gfm-parity.md`)
- Slug collision handling changes

## Design Decisions

## Open Questions

- Should the regex use `\w` (which is unicode-aware in Python 3) or
  a more explicit unicode category pattern?
- Does the existing slug collision logic (appending `-1`, `-2`) need
  adjustment for unicode normalization (e.g., NFC vs NFD)?
