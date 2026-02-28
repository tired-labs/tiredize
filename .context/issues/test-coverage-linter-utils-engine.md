Status: ready
Parent: test-coverage-audit.md

# Test Coverage: Linter Utils and Engine

## Summary

Write tests for `tiredize/linter/utils.py` config helpers and
`check_url_valid` HTTP/anchor paths, plus fill gaps in
`tiredize/linter/engine.py`. Part of the test coverage audit
(`test-coverage-audit.md`).

## Acceptance Criteria

### Config helpers (0% coverage today)

- [ ] `get_config_int` -- correct type returns value, wrong type
      returns None, missing key returns None, bool input returns None
      (bool is subclass of int)
- [ ] `get_config_str` -- correct type returns value, wrong type
      returns None, missing key returns None
- [ ] `get_config_bool` -- correct type returns value, wrong type
      returns None, missing key returns None
- [ ] `get_config_dict` -- correct type returns value, wrong type
      returns None, missing key returns None
- [ ] `get_config_list` -- correct type returns value, wrong type
      returns None, missing key returns None

### check_url_valid anchor path (0% coverage today)

- [ ] Anchor found in document sections -- returns (True, None, None)
- [ ] Anchor not found -- returns (False, None, "anchor not found...")
- [ ] Document with no sections -- returns not found

### check_url_valid HTTP path (0% coverage today, use unittest.mock)

- [ ] Successful response (2xx) -- mock requests.get to return 200,
      verify (True, 200, None)
- [ ] Redirect response (3xx) -- mock 301, verify (True, 301, None)
- [ ] Client error (4xx) -- mock 404, verify (False, 404, None)
- [ ] Server error (5xx) -- mock 500, verify (False, 500, None)
- [ ] Timeout -- mock requests.exceptions.Timeout, verify
      (False, None, "timeout")
- [ ] Connection error -- mock requests.exceptions.ConnectionError,
      verify (False, None, error string)
- [ ] Custom headers passed through -- verify mock receives headers
- [ ] Custom timeout passed through -- verify mock receives timeout
- [ ] allow_redirects defaults to True when None

### engine.py gaps (92% coverage today)

- [ ] `run_linter` with `rule_configs=None` -- returns empty list
      (line 24)
- [ ] `run_linter` with non-dict rule config value -- raises
      ValueError (line 58)
- [ ] Line 64 (invalid Rule object) -- document as unreachable in
      test file if confirmed unreachable

### rules/__init__.py gaps (96% coverage today)

- [ ] Line 37 (package with no `__path__`) -- determine if reachable
      and test or document
- [ ] Line 45 (subpackage skipping) -- test with a package containing
      a subpackage

### State mutation (audit point 8)

- [ ] `check_url_valid` does not mutate the Document it receives --
      assert document attributes are unchanged after the call
- [ ] `run_linter` does not mutate the rule_configs dict -- assert
      configs are unchanged after the call
- [ ] `get_config_*` helpers do not mutate the config dict -- assert
      unchanged after each call

### Unicode and non-ASCII (audit point 9)

- [ ] Anchor slug with non-ASCII characters (e.g., `#café-section`)
      -- verify anchor matching works correctly
- [ ] Relative path with non-ASCII filename -- verify path resolution
      handles unicode filenames

### Partial failure in collections (audit point 10)

- [ ] `run_linter` with multiple rules where rule 2 of 3 raises an
      unexpected exception -- verify whether rules 1 and 3 still
      produce results or the entire call fails. Document actual
      behavior.

### Review existing tests for completeness

- [ ] Review `test_utils.py` (relative URL tests) -- verify the 3
      existing tests from `fix-relative-url-resolution` are complete.
      Add missing edge cases if found.

### Coverage target

- [ ] 100% coverage on `tiredize/linter/utils.py`,
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

## Open Questions
