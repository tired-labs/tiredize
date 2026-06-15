---
assignee:
created: 2026-06-15
knowledge: []
priority: medium
status: draft
step:
tags: [cli, exit-code, validation]
type: bug
workflow: software-engineering
---

# `python -m tiredize` Always Exits 0

## Summary

`tiredize/__main__.py` calls `main()` without propagating its return value
as the process exit code:

    from tiredize.cli import main
    main()

`main()` returns the intended exit code (`0` = clean, `1` = findings or
error, `2` = usage error), but `__main__.py` discards it, so the process
**always exits 0** — validation findings, missing files, bad schemas, and
usage errors alike. As a result `python -m tiredize` can never signal
failure and is unusable as a CI or pre-commit gate.

The `tiredize` console-script entry point is unaffected: setuptools wraps
it as `sys.exit(main())`, so it exits with the correct code. CI that uses
the console script (`.github/workflows/validate-issues.yml`) still gates
correctly; only the `-m` invocation is broken.

This blocks invoking self-validation via `python -m tiredize` in the local
pre-commit hook, where module invocation is used for consistency with how
flake8 and pytest are called.

## Acceptance Criteria

- [ ] `python -m tiredize` exits with `main()`'s return code: `1` on
      findings or errors, `2` on usage error, `0` when clean
- [ ] `tiredize/__main__.py` propagates the exit code
      (e.g. `raise SystemExit(main())`)
- [ ] A test covers `python -m tiredize` exit codes for clean input,
      input with findings, and the usage error
- [ ] Console-script behavior is unchanged

## Design Decisions

<!-- To be filled during scoping. -->

## Open Questions

None — the fix is well understood; kept `draft` pending prioritization.

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Found during the tiredize `.context/` readiness assessment while
    checking why self-validation was not running locally. The console
    script exits correctly; only `python -m tiredize` is broken. This is a
    prerequisite for invoking self-validation via `python -m tiredize` in
    the local pre-commit hook.
