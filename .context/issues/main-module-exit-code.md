---
assignee: user
created: 2026-06-15
knowledge: []
priority: medium
status: in-progress
step: scoping
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
the usage error alike. As a result `python -m tiredize` can never signal
failure and is unusable as a CI or pre-commit gate.

The `tiredize` console-script entry point is unaffected: the generated
wrapper calls `sys.exit(main())`, so it exits with the correct code. CI
that uses the console script (`.github/workflows/validate-issues.yml`)
still gates correctly; only the `-m` invocation is broken.

This blocks invoking self-validation via `python -m tiredize` in the local
pre-commit hook, where module invocation is used for consistency with how
flake8 and pytest are called.

### Observed Behavior

Verified on the current `main` (all commands run from the repository
root):

| Invocation                                             | Exit |
|--------------------------------------------------------|------|
| `python -m tiredize` (no arguments)                      | 0    |
| `python -m tiredize --markdown-schema s.yaml clean.md`   | 0    |
| `python -m tiredize --markdown-schema s.yaml bad.md`     | 0    |
| `python -m tiredize --markdown-schema s.yaml missing.md` | 0    |
| `python -m tiredize --bogus doc.md`                      | 2    |

Only the last case is correct today, and only incidentally: argparse
raises `SystemExit(2)` from inside `main()`, so it never reaches the
discarded return value. Every code path that *returns* a status is lost.

### Public Contract

The change fixes the process exit status of the `-m` invocation. Nothing
else about the interface changes.

**Interface.** `python -m tiredize [OPTIONS] [PATHS...]` — identical
argument surface to the `tiredize` console script, because both dispatch
to `tiredize.cli:main`.

**Inputs.** Unchanged: `--rules`, `--markdown-schema`,
`--frontmatter-schema`, and zero or more positional markdown paths.

**Process exit status.** After the fix, `python -m tiredize` must exit
with exactly the integer `tiredize.cli.main()` returns:

- `0` — every path was loaded and produced no findings.
- `1` — at least one path produced findings, or a runtime error occurred
  (input file missing, configuration file missing or unparseable, unknown
  rule id, ambiguous schema).
- `2` — usage error: no positional paths were given, or none of the three
  configuration flags was given.

Argparse's own errors (unknown flag, missing flag value) continue to exit
`2` by raising `SystemExit` from within `main()`; that path is already
correct and must stay correct.

**Output streams.** Unchanged. Findings print to stdout as
`path:line:col: [rule_id] message`; the per-file `path: no issues found.`
line prints to stdout; runtime errors and the usage message print to
stderr. For any given argument list, `python -m tiredize` and `tiredize`
must produce the same stdout, the same stderr, and now the same exit
status.

**Console script.** Unchanged in every respect.

## Acceptance Criteria

- [ ] `python -m tiredize` exits with exactly the value returned by
      `tiredize.cli.main()`: `0` when all paths are clean, `1` on findings
      or runtime error, `2` on usage error
- [ ] `tiredize/__main__.py` propagates the return value of `main()` as
      the process exit status (e.g. `raise SystemExit(main())`)
- [ ] An automated test invokes `python -m tiredize` as a subprocess and
      asserts the exit status for three cases: clean input (`0`), input
      with findings (`1`), and the usage error with no arguments (`2`)
- [ ] Console-script behavior is unchanged: the existing `tests/test_cli.py`
      suite passes without modification
- [ ] `python -m tiredize` and `tiredize` produce identical stdout and
      stderr for the same arguments

## Design Decisions

### Scope of the fix

The defect is confined to `tiredize/__main__.py`. `tiredize.cli.main()`
already returns the correct codes and is not to be changed — every
existing exit-code test in `tests/test_cli.py` must keep passing
untouched. `pyproject.toml` and the `[project.scripts]` entry point are
not touched either.

### Fix idiom

Prefer `raise SystemExit(main())`, matching the idiom already used at the
bottom of `tiredize/cli.py`. `sys.exit(main())` is functionally
equivalent; the preference is repository consistency, not correctness.
The engineer may deviate with a recorded reason.

### Test approach

The exit status of `python -m tiredize` is only observable from another
process — importing `tiredize.__main__` executes it at import time and
gives no process status to assert on. The test must therefore spawn a
subprocess with `sys.executable -m tiredize`. Running with `cwd` set to
the repository root is sufficient for the package to be importable, which
matches how CI and the local pre-commit hook invoke it.

### Test file naming

`.context/PYTHON.md` says a test for `<package>/foo/bar.py` belongs at
`tests/foo/test_bar.py`. Applied literally that yields
`tests/test___main__.py`, which is unreadable. A clearer equivalent such
as `tests/test_main_module.py` is acceptable; whichever name is chosen,
record it in the issue comments so review does not relitigate it.

### Out of scope

- Changing the exit-code semantics of `main()` itself.
- Adding the self-validation invocation to `.githooks/pre-commit`. That
  is the motivation for this fix, not part of it, and belongs in a
  separate issue once `-m` gates correctly.
- Authoring a CLI entry-point specification. `.context/specifications/`
  covers the parser, linter, and both validators but has no document for
  the CLI or its exit-code contract. That is a pre-existing gap, noted
  here for triage; the step-6 architect decides whether this issue is the
  right place to close it.

### Scoping seeds

These seed the technical-architect's later judgment. They are seeds, not
commitments — the architect makes the final calls at steps 6 and 7.

**Step 6 — does this change a subsystem's behavior or public contract?
Seed: yes.** The observable process exit status of a public entry point
changes for three of its four failure modes. The nuance the architect
must weigh: the fix restores the contract `main()` was always written to
express rather than designing a new one, and no existing specification
documents the CLI at all, so "update the spec" has nothing to update. The
architect chooses between authoring a CLI entry-point spec and recording
that no specification change is warranted for a one-line restoration.

**Step 7 — does this need user-facing documentation? Seed: yes.** The
README's Usage section documents only the console script and describes
exit behavior loosely as "returns a nonzero exit code when validation
fails." It never distinguishes `1` from `2`, and never mentions
`python -m tiredize`. This fix makes the module invocation usable as a CI
and pre-commit gate, which is precisely the use the README's Usage
section is pitched at, so the exit-code contract is worth stating
explicitly there.

## Open Questions

None. The exit-code contract is specified above and the fix is
well understood.

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Found during the tiredize `.context/` readiness assessment while
    checking why self-validation was not running locally. The console
    script exits correctly; only `python -m tiredize` is broken. This is a
    prerequisite for invoking self-validation via `python -m tiredize` in
    the local pre-commit hook.

### 2026-09-05T00:00:00+00:00

Author: program-manager/software-engineering

    Scoping complete. Confirmed the reported behavior by running each
    invocation against the current `main`; results are in the Observed
    Behavior table. One correction to the original report: the usage-error
    path is broken like the others (it returns `2`, which is discarded),
    while argparse's own errors already exit `2` correctly because they
    raise `SystemExit` rather than returning. The acceptance criteria were
    tightened to name checkable outcomes, the public contract was written
    out so acceptance tests can be authored against it without reading the
    implementation, and both scoping seeds are recorded.

    The absence of any CLI specification under `.context/specifications/`
    is a pre-existing gap, logged in Design Decisions for triage rather
    than acted on here.

    Awaiting user approval of the scope and contract before acceptance
    test design begins.
