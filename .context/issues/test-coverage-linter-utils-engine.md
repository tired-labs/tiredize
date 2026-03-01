Status: completed
Parent: test-coverage-audit.md

# Test Coverage: Linter Utils and Engine

## Summary

Write tests for `tiredize/linter/utils.py` config helpers and
`check_url_valid` HTTP/anchor paths, plus fill gaps in
`tiredize/linter/engine.py`. Part of the test coverage audit
(`test-coverage-audit.md`).

## Acceptance Criteria

### Config helpers (0% coverage today)

- [x] `get_config_int` -- correct type returns value, wrong type
      returns None, missing key returns None, bool input returns None
      (bool is subclass of int)
- [x] `get_config_str` -- correct type returns value, wrong type
      returns None, missing key returns None
- [x] `get_config_bool` -- correct type returns value, wrong type
      returns None, missing key returns None
- [x] `get_config_dict` -- correct type returns value, wrong type
      returns None, missing key returns None
- [x] `get_config_list` -- correct type returns value, wrong type
      returns None, missing key returns None

### check_url_valid anchor path (0% coverage today)

- [x] Anchor found in document sections -- returns (True, None, None)
- [x] Anchor not found -- returns (False, None, "anchor not found...")
- [x] Document with no sections -- returns not found

### check_url_valid HTTP path (0% coverage today, use unittest.mock)

- [x] Successful response (2xx) -- mock requests.get to return 200,
      verify (True, 200, None)
- [x] Redirect response (3xx) -- mock 301, verify (True, 301, None)
- [x] Client error (4xx) -- mock 404, verify (False, 404, None)
- [x] Server error (5xx) -- mock 500, verify (False, 500, None)
- [x] Timeout -- mock requests.exceptions.Timeout, verify
      (False, None, "timeout")
- [x] Connection error -- mock requests.exceptions.ConnectionError,
      verify (False, None, error string)
- [x] Custom headers passed through -- verify mock receives headers
- [x] Custom timeout passed through -- verify mock receives timeout
- [x] allow_redirects defaults to True when None

### engine.py gaps (92% coverage today)

- [x] `run_linter` with `rule_configs=None` -- returns empty list
      (line 24)
- [x] `run_linter` with non-dict rule config value -- raises
      ValueError (line 58)
- [x] Line 64 (invalid Rule object) -- document as unreachable in
      test file if confirmed unreachable

### rules/__init__.py gaps (96% coverage today)

- [x] Line 37 (package with no `__path__`) -- determine if reachable
      and test or document
- [x] Line 45 (subpackage skipping) -- test with a package containing
      a subpackage

### State mutation (audit point 8)

- [x] `check_url_valid` does not mutate the Document it receives --
      assert document attributes are unchanged after the call
- [x] `run_linter` does not mutate the rule_configs dict -- assert
      configs are unchanged after the call
- [x] `get_config_*` helpers do not mutate the config dict -- assert
      unchanged after each call

### Unicode and non-ASCII (audit point 9)

- [x] Anchor slug with non-ASCII characters (e.g., `#café-section`)
      -- verify anchor matching works correctly
- [x] Relative path with non-ASCII filename -- verify path resolution
      handles unicode filenames

### Partial failure in collections (audit point 10)

- [x] `run_linter` with multiple rules where rule 2 of 3 raises an
      unexpected exception -- verify whether rules 1 and 3 still
      produce results or the entire call fails. Document actual
      behavior.

### Review existing tests for completeness

- [x] Review `test_utils.py` (relative URL tests) -- verify the 3
      existing tests from `fix-relative-url-resolution` are complete.
      Add missing edge cases if found.

### Coverage target

- [x] 100% coverage on `tiredize/linter/utils.py`,
      `tiredize/linter/engine.py`, and
      `tiredize/linter/rules/__init__.py`, or documented exclusions

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Writing new tests for rule module validate() functions (covered by
  `test-coverage-linter-rules.md`)
- Writing new tests for markdown element types (covered by
  `test-coverage-markdown-types.md`)

## Design Decisions

- HTTP tests use `unittest.mock.patch` on `requests.get` rather than
  a dedicated mocking library. This avoids adding a test dependency
  and is sufficient for testing our branching logic.
- `get_config_int` does NOT reject bools. Because `bool` is a
  subclass of `int` in Python, `isinstance(True, int)` is `True`
  and the function returns the bool value. The spec-correct test
  asserts `None` and is skipped pending a fix (add a `bool` guard
  before the `int` isinstance check).
- `slugify_header` strips all non-ASCII characters via the regex
  `[^a-z0-9 \-]`. GFM preserves non-ASCII in slugs. The
  spec-correct anchor test asserts GFM behavior and is skipped
  pending a unicode-aware slugifier.
- engine.py line 64 (`isinstance(rule, Rule)` guard) is unreachable
  from the public API. `_select_rules` always stores a genuine Rule
  object from the discovered rules dict. Documented in the test file
  as a comment rather than tested.
- `rules/__init__.py` line 37 and line 45 were already covered by
  tests added in the `test-coverage-linter-rules` sub-issue
  (`test_discover_rules_plain_module_returns_empty` and
  `test_discover_rules_skips_subpackages`).
- `run_linter` does not catch exceptions from rule `validate()`
  functions. An unexpected exception propagates and remaining rules
  are not executed.

## Follow-up Issues

- `fix-config-int-bool-guard.md` -- `get_config_int` accepts bool
  inputs due to Python's `bool` subclassing `int`. Skipped spec test
  awaits fix.
- `fix-slug-non-ascii.md` -- `slugify_header` strips non-ASCII
  characters. GFM preserves them. Skipped spec test awaits fix.

## Open Questions
