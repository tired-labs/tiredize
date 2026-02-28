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

## Design Decisions

## Open Questions

- Should tests that are found missing be written to match the existing
  code behavior (characterization tests), or should they be written to
  match the intended behavior from the specifications?
- What is the target coverage threshold? 100% with documented
  exclusions, or a lower bar?
