Status: completed

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

- [x] `slugify_header` preserves non-ASCII letters (accented, CJK,
      etc.) while still removing punctuation
- [x] "Café Section" produces `#café-section`, not `#caf-section`
- [x] The skipped test `test_anchor_with_non_ascii_slug` is unskipped
      and passes
- [x] All existing tests pass (no regressions)
- [x] Markdown parser specification updated to document slug
      generation rules including non-ASCII handling

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Full GFM parity (tracked in `gfm-parity.md`)
- Slug collision handling changes

## Design Decisions

- Use `\w` (Python 3 unicode-aware): `r"[^\w \-]"`. This keeps
  Unicode letters, digits, and underscores while stripping punctuation,
  matching GFM behavior for NFC text. `\w` excludes Unicode combining
  marks (category M), so NFD-decomposed diacritics are stripped — a
  known limitation, not worth the complexity of a `unicodedata`-based
  filter for an edge case that is vanishingly rare in real markdown.
  Chosen over explicit Unicode ranges (fragile, incomplete) and the
  third-party `regex` module (unnecessary dependency).
- No Unicode normalization (NFC/NFD). No normalization step is
  applied before slug generation — the implementation operates on
  the Unicode string as received. NFC text (the common form) is
  handled correctly. NFD combining marks are stripped due to the
  `\w` limitation above. Mixed normalization forms in a single
  document are extremely rare. If NFD support becomes a real
  problem, it can be its own issue.

## Open Questions
