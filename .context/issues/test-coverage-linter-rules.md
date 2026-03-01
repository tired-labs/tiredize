Status: active
Parent: test-coverage-audit.md

# Test Coverage: Linter Rules

## Summary

Write full test suites for the three linter rule modules currently at
22-26% coverage (links, tabs, trailing_whitespace) and fill the CRLF
gap in line_length. Part of the test coverage audit
(`test-coverage-audit.md`).

## Acceptance Criteria

### tabs.py (25% coverage today)

- [x] Tab detected, not allowed -- single tab, multiple tabs on one
      line, tabs on multiple lines
- [x] Tab detected, allowed -- returns no violations
- [x] Tab position accuracy -- verify reported offset matches actual
      tab position in document
- [x] Config missing `allowed` key -- verify behavior (returns None
      from get_config_bool, which is falsy)
- [x] Config `allowed` wrong type -- verify behavior
- [x] Empty document -- no violations
- [x] CRLF line endings -- verify tab detection handles `\r\n`

### trailing_whitespace.py (26% coverage today)

- [x] Trailing spaces detected, not allowed -- single space, multiple
      spaces, trailing tab
- [x] Trailing whitespace detected, allowed -- returns no violations
- [x] Position accuracy -- verify reported offset matches trailing
      whitespace start
- [x] Config missing `allowed` key -- verify behavior
- [x] Config `allowed` wrong type -- verify behavior
- [x] Empty document -- no violations
- [x] Line with only whitespace -- verify full line reported as
      trailing
- [x] CRLF line endings -- verify detection handles `\r\n`

### links.py (22% coverage today)

- [x] Config `validate` is false or missing -- returns empty results
- [x] Config `validate` is true with no links in document -- returns
      empty results
- [x] Inline link valid -- mock `check_url_valid` to return success
- [x] Inline link invalid -- mock returns failure with error message
- [x] Bracket link valid and invalid -- same mock pattern
- [x] Bare link valid and invalid -- same mock pattern
- [x] Reference definition valid and invalid -- same mock pattern
- [x] Multiple link types in same section -- all checked
- [x] Config `timeout` and `headers` passed through to
      `check_url_valid`
- [x] Use `unittest.mock.patch` to mock `check_url_valid`, not HTTP
      requests directly

### line_length.py (96% coverage today)

- [x] CRLF line endings -- verify line length excludes `\r\n`
      (line 37: `\r` stripping path)

### Cross-component interactions (audit point 5)

- [x] Links rule: same URL appears as both InlineLink and BareLink in
      same section -- verify both are checked (or document if
      deduplicated)
- [x] Links rule: document with multiple sections containing links --
      verify all sections are iterated, not just the first

### Idempotency (audit point 7)

- [x] Run each rule's validate() twice on the same document -- verify
      identical results both times (rules should be pure functions)

### State mutation (audit point 8)

- [x] Each rule's validate() does not mutate the Document it receives
      -- assert document.string and section data are unchanged after
      the call
- [x] Each rule's validate() does not mutate the config dict --
      assert config is unchanged after the call

### Unicode and non-ASCII (audit point 9)

- [x] tabs.py: line containing tabs mixed with non-ASCII characters --
      verify tab positions are correct (character index, not byte)
- [x] trailing_whitespace.py: trailing spaces after non-ASCII content
      -- verify position accuracy
- [x] line_length.py: line with multi-byte characters -- verify length
      is measured in characters, not bytes
- [x] links.py: link with unicode URL -- verify it reaches
      check_url_valid with the URL intact

### Partial failure in collections (audit point 10)

- [x] links.py: mock check_url_valid to raise an unexpected exception
      on link 2 of 3 -- verify whether link 3 is still checked or the
      rule crashes. Document actual behavior.
- [x] tabs.py and trailing_whitespace.py: less relevant since they
      iterate lines without external calls, but verify a document with
      many lines processes all of them (no early termination)

### Review existing tests for completeness

- [x] Review `test_engine.py` -- verify run_linter and _select_rules
      tests cover all branching logic (no rules, all rules, subset,
      invalid rule IDs, empty/None configs). Add missing tests.
- [x] Review `test_loader.py` -- verify discover_rules tests cover
      happy path, edge cases (no rules, private modules, subpackages).
      Add missing tests.

### Coverage target

- [x] 100% coverage on all four rule modules, or documented exclusions
      for unreachable lines

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Writing new tests for `check_url_valid()` (covered by
  `test-coverage-linter-utils-engine.md`)
- Writing new tests for markdown element extraction (covered by
  `test-coverage-markdown-types.md`)

## Design Decisions

- Links rule tests mock `check_url_valid` rather than `requests.get`.
  This tests the rule's branching logic (which link types are checked,
  how results are reported) without coupling to HTTP internals. HTTP
  path coverage for `check_url_valid` itself belongs in the linter
  utils/engine sub-issue.
- The links rule does not catch unexpected exceptions from
  `check_url_valid`. If `check_url_valid` raises, the rule propagates
  the exception and remaining links are not checked. This is documented
  behavior, not a bug -- error handling belongs in the caller or in
  `check_url_valid` itself.
- engine.py has two defensive `ValueError` guards (lines 58, 64) that
  are unreachable from the public API. `_select_rules` guarantees the
  types. These are not tested and are excluded from coverage targets.

## Open Questions
