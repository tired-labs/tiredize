Status: draft

# Fix get_config_int to reject bool inputs

## Summary

`get_config_int()` in `tiredize/linter/utils.py` accepts `bool` values
because Python's `bool` is a subclass of `int` (`isinstance(True, int)`
is `True`). A bool config value is semantically different from an
integer -- `True` should not be treated as `1`. The function should
return `None` for bool inputs, consistent with the type-safe contract
described in the linter specification.

Discovered during the test coverage audit
(`test-coverage-linter-utils-engine.md`). A spec-correct test exists
and is currently skipped:
`tests/linter/test_utils.py::test_get_config_int_bool_returns_none`.

## Acceptance Criteria

- [ ] `get_config_int` returns `None` when the value is a `bool`
      (add `isinstance(raw_value, bool)` guard before the `int` check)
- [ ] The skipped test `test_get_config_int_bool_returns_none` is
      unskipped and passes
- [ ] All existing tests pass (no regressions)
- [ ] Linter specification verified -- already says "wrong type returns
      None" which covers this fix

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

## Design Decisions

## Open Questions
