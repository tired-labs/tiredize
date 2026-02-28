Status: active
Sub-issues:
  - test-coverage-markdown-types.md
  - test-coverage-markdown-utils.md
  - test-coverage-linter-rules.md
  - test-coverage-linter-utils-engine.md

# Test Coverage Audit for Linter and Markdown Packages

## Summary

Audit unit tests across `tiredize/linter` and `tiredize/markdown` for
completeness. The original tests were written manually without
systematic coverage analysis. This issue ensures every code path has
proper base case, edge case, and boundary coverage.

This is a parent issue. The work is split into four sub-issues. This
issue is not closed until all sub-issues are complete and every test
file in the linter and markdown packages has been reviewed.

## Sub-Issues

- `test-coverage-markdown-types.md` -- Element type tests: new test
  files for links, references, list stub; sanitize method tests;
  cross-type interaction tests; review of all existing element type
  test files
- `test-coverage-markdown-utils.md` -- Direct tests for search_all_re
  and sanitize_text
- `test-coverage-linter-rules.md` -- Full test suites for links, tabs,
  trailing_whitespace rules; CRLF gap in line_length; review of
  existing engine and loader tests
- `test-coverage-linter-utils-engine.md` -- Config helper tests;
  check_url_valid anchor/HTTP paths; engine gaps; review of existing
  relative URL tests

## Acceptance Criteria

- [ ] All four sub-issues completed
- [ ] Every existing test file in `tests/linter/` and
      `tests/markdown/` has been reviewed for completeness and updated
      where gaps were found (not just new test files -- existing tests
      must be audited too)
- [ ] 100% coverage across `tiredize/linter/` and
      `tiredize/markdown/`, or documented exclusions for unreachable
      lines
- [ ] Fix any bugs discovered during the audit
- [ ] Final coverage report comparing before and after

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

- Tests are written to match specification behavior, not current code
  behavior. If code doesn't match the spec, fix the code as part of
  this audit (within the "fix bugs found during audit" criterion).
- Target is 100% coverage with documented exclusions for unreachable
  lines. No lower bar.
- Full test suites for undertested rule modules, not just gap-filling.
- HTTP mocking uses `unittest.mock` (standard library), no new
  dependencies.
- Cross-type interaction tests in the markdown types sub-issue
  document actual parser behavior. False positives caused by missing
  sanitization are asserted with comments noting the known gap, not
  fixed (sanitization fixes belong in `parser-sanitization-audit.md`).

## Open Questions
