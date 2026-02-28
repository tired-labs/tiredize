Status: draft

# Test Coverage Audit for Linter and Markdown Packages

## Summary

Audit unit tests across `tiredize/linter` and `tiredize/markdown` for
completeness. The original tests were written manually without
systematic coverage analysis. This issue ensures every code path has
proper base case, edge case, and boundary coverage.

## Acceptance Criteria

- [ ] Audit `tiredize/markdown/types/` tests -- for each element type,
      verify tests cover: basic extraction, multiple matches, no
      matches, edge cases (empty input, malformed syntax, nested
      constructs), and sanitize method correctness
- [ ] Audit `tiredize/markdown/utils.py` tests -- verify
      `search_all_re`, `get_position_from_match`, and `sanitize_text`
      have base case, edge case, and error path coverage
- [ ] Audit `tiredize/markdown/types/document.py` tests -- verify
      `Document.load()`, `Document.line_col()`, and `_parse()` cover
      file loading, text loading, empty documents, and position
      accuracy
- [ ] Audit `tiredize/linter/engine.py` tests -- verify `run_linter`
      and `_select_rules` cover: no rules, all rules, subset of
      rules, invalid rule IDs, empty configs, None configs
- [ ] Audit `tiredize/linter/rules/` tests -- for each rule module,
      verify tests cover: violation detected, no violation, boundary
      values, missing config keys, wrong config types
- [ ] Audit `tiredize/linter/utils.py` tests -- verify config helpers
      cover: correct type, wrong type, missing key; verify
      `check_url_valid` covers: anchors, relative paths, HTTP URLs,
      timeouts, connection errors
- [ ] Run coverage and identify untested lines; add tests or document
      why lines are unreachable
- [ ] Fix any bugs discovered during the audit

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Schema validator tests (already audited as part of
  `markdown-schema-validation.md`)
- CLI tests (already audited as part of `markdown-schema-validation.md`)
- Sanitization chain audit (covered by `parser-sanitization-audit.md`)
- Code changes beyond what is needed to fix bugs found during audit

## Known Gaps Discovered Before Audit

These gaps were found during other work and should be verified and
addressed as part of the audit:

- `tiredize/linter/utils.py` -- `check_url_valid()` had zero test
  coverage prior to `fix-relative-url-resolution`. The relative URL
  path now has 3 tests; anchor validation, HTTP validation,
  `get_config_*` helpers, timeout handling, and connection error paths
  remain untested (lines 20-75, 103-106, 118-144).
- `tiredize/linter/utils.py` -- Relative URLs without a `./` or `../`
  prefix (e.g., `sibling.md`) fall through to the HTTP branch. See
  issue `relative-url-prefix-handling.md`.
- `tiredize/markdown/types/schema.py` -- Level bounds validation
  (`1 <= level <= 6`) was added as a bug fix during Copilot review
  feedback. Four tests exist but should be reviewed for completeness
  during the audit.

## Design Decisions

## Open Questions

- Should tests that are found missing be written to match the existing
  code behavior (characterization tests), or should they be written to
  match the intended behavior from the specifications?
- What is the target coverage threshold? 100% with documented
  exclusions, or a lower bar?
