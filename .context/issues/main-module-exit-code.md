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
- `1` — at least one path produced findings, or a runtime error occurred.
- `2` — usage error: no positional paths were given, or none of the three
  configuration flags was given.

Exit `1` covers two distinct categories, which differ in how they affect
the rest of the run:

*Findings* — a linter rule violation (line length, unreachable URL,
disallowed unicode), a markdown schema mismatch (a required section
missing, sections out of order, wrong heading level), or a frontmatter
schema violation (missing required field, wrong type, disallowed value).

*Runtime errors* — an input document that does not exist, a
configuration file that is missing or unparseable, an unknown rule id, or
an ambiguous schema.

**Processing semantics.** Findings do not stop the run: every path is
processed, every finding is reported, and the process exits `1` at the
end. Runtime errors do stop the run: the first one prints to stderr and
the process exits `1` immediately, leaving any remaining paths
unprocessed.

This changes current behavior. Today a missing input document sets the
exit code and *continues* to the next path (cli.py:114–122), while
configuration errors abort. After this change all runtime errors abort,
so the rule is uniform: errors abort, findings continue. The change
applies to `main()` and therefore to both entry points.

Argparse's own errors (unknown flag, missing flag value) continue to exit
`2` by raising `SystemExit` from within `main()`; that path is already
correct and must stay correct.

**Output streams.** Findings print to stdout as
`path:line:col: [rule_id] message`; the per-file `path: no issues found.`
line prints to stdout; runtime errors and the usage message print to
stderr. For any given argument list, `python -m tiredize` and `tiredize`
must produce the same stdout, the same stderr, and the same exit status.

**Console script.** Its wiring is unchanged and it keeps exiting with
`main()`'s return value. Its observable behavior changes only where
`main()`'s abort semantics change, above.

## Acceptance Criteria

- [ ] `python -m tiredize` exits with exactly the value returned by
      `tiredize.cli.main()`: `0` when all paths are clean, `1` on findings
      or runtime error, `2` on usage error
- [ ] `tiredize/__main__.py` propagates the return value of `main()` as
      the process exit status (e.g. `raise SystemExit(main())`)
- [ ] An automated test invokes `python -m tiredize` as a subprocess and
      asserts the exit status for three cases: clean input (`0`), input
      with findings (`1`), and the usage error with no arguments (`2`)
- [ ] Every test already in `tests/test_cli.py` passes unchanged. New
      tests may be added to that file; existing ones may not be edited or
      deleted
- [ ] `python -m tiredize` and `tiredize` produce identical stdout and
      stderr for the same arguments
- [ ] A runtime error aborts the run: given several paths where an earlier
      one is a missing input document, no later path is processed and the
      process exits `1`. Verified for both `python -m tiredize` and the
      console script
- [ ] `.context/schemas/issue-frontmatter.yaml` allows
      `assignee: program-manager` in place of `PM`,
      `.context/issues/context-process-migration.md` is updated to match,
      and every file in `.context/issues/` validates clean
- [ ] `.context/specifications/cli.md` exists, follows
      `templates/SPECIFICATION.md`, and documents the exit-code contract
      including the findings-continue and errors-abort semantics

## Design Decisions

### Scope of the fix

The *propagation* defect is confined to `tiredize/__main__.py`.
`tiredize.cli.main()` already returns the correct codes, so no change to
its return values is needed. Its abort semantics do change, separately —
see "Errors abort the run" below. `pyproject.toml` and the
`[project.scripts]` entry point are not touched.

### Errors abort the run

Today `main()` treats a missing input document as a per-document problem:
it prints the error, sets `exit_code = 1`, and continues to the next path
(cli.py:114–122). Configuration errors abort instead. This issue makes
all runtime errors abort, so the rule becomes uniform — errors abort,
findings continue.

Two principles were weighed. The current code follows "per-document
problems continue, global problems abort," which lets a batch run over
many files report on the survivors. The chosen rule is "errors abort,
findings continue," which is one rule rather than two axes and makes the
exit-code contract predictable without knowing which category an error
falls into. The user chose the latter, having heard the batch-validator
argument for keeping the current behavior.

Consequences to respect downstream: this changes `main()`, so the
console script's observable behavior changes too, not just the `-m`
invocation. It is not a pure propagation fix any more.

No existing test pins the behavior being changed.
`tests/test_nonexistent_document_path` (test_cli.py:247) passes a single
path and asserts only `result == 1`, which still holds under abort; no
test combines a missing document with other paths. That is why the
"passes without modification" criterion survives the change.

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

### Test file naming and organization

`.context/PYTHON.md` says a test for `<package>/foo/bar.py` belongs at
`tests/foo/test_bar.py`. Applied literally that yields
`tests/test___main__.py`, which is unreadable. Use
`tests/test_main_module.py` instead and do not relitigate the name at
review.

**One file, not two.** The mirror rule is one test file per source
module, and `tiredize/__main__.py` is one module. Both tiers of test live
in `tests/test_main_module.py`, separated by test classes — the idiom
already used in `tests/validators/test_frontmatter_schema.py`, which
groups ten concerns into one file. Suggested split:

- `TestExitStatus` — the step-2 acceptance tests. Black-box, subprocess,
  asserting process exit status against the contract.
- `TestModuleExecution` — the step-3 white-box tests. In-process, for
  branch coverage of the module body.

Name the classes so the tier each belongs to is obvious from the outside.
The step-5 verifier has to identify the acceptance tests without being
told, and two agents write into this file at different steps: the
qa-engineer creates it at step 2, the software-engineer adds to it at
step 3 without editing what step 2 wrote.

### Covering `tiredize/__main__.py`

The module currently reports 0% coverage because nothing executes it.
Importing it runs `main()` at import time, and the subprocess tests
required by the acceptance criteria run in a different process, which the
parent's coverage does not measure.

Step 3 should add an in-process test that executes the module body via
`runpy.run_module("tiredize", run_name="__main__")` with `sys.argv`
patched, asserting on the resulting `SystemExit.code`. This is a
code-level test, not an acceptance test, which is why it belongs to the
software-engineer at step 3 rather than the qa-engineer at step 2.

Rejected alternatives: configuring coverage to measure subprocesses
(`parallel = true` plus `COVERAGE_PROCESS_START`) adds machinery and a
known flakiness source for no extra behavioral proof; omitting the file
from coverage would hide a gap that is straightforward to close. The
project sets no coverage threshold, so this is about not leaving a
visible hole rather than satisfying a gate.

### Seed the CLI specification here

`.context/specifications/` covers the parser, linter, and both validators
but has no document for the CLI. Rather than leave the exit-code contract
with nowhere to live, this issue creates `.context/specifications/cli.md`
and populates it with the exit-code contract only. It is a foundation to
build on, not a complete CLI specification — flags, output format, and
configuration resolution are documented as later issues touch them. The
Overview should say plainly that the document is partial, so a reader
does not mistake silence for absence of behavior.

This directs an outcome the workflow would normally leave to the
technical-architect at step 6. The architect no longer decides *whether*
a specification is warranted; the acceptance criteria require one. The
architect still owns its content, structure, and how it conforms to
`templates/SPECIFICATION.md`.

### Folding in the assignee vocabulary fix

`.context/schemas/issue-frontmatter.yaml` allows `assignee: PM` while the
workflow files, function filenames, and the `AGENTS.md` knowledge map all
use `program-manager`. Every other allowed value already matches a
function filename, so `PM` is the lone exception, and an agent setting
`assignee: program-manager` would fail the project's own validation.

This is unrelated to the exit-code defect and would normally be a
separate task. It was folded in deliberately: the change is two lines
across two files, it affects no other workflow, and it unblocks correct
assignee values on the very next step of this issue. The scope-discipline
objection was raised and overruled by the user.

### Out of scope

- Adding the self-validation invocation to `.githooks/pre-commit`. That
  is the motivation for this fix, not part of it, and belongs in a
  separate issue once `-m` gates correctly.
- Expanding `cli.md` beyond the exit-code contract.

### Scoping seeds

These seed the technical-architect's later judgment. They are seeds, not
commitments — the architect makes the final calls at steps 6 and 7.

**Step 6 — does this change a subsystem's behavior or public contract?
Directed: yes, author the specification.** The observable exit status of
a public entry point changes for three of its four failure modes, and
`main()`'s abort semantics change on top of that. Because no
specification documents the CLI at all, the acceptance criteria require
authoring `.context/specifications/cli.md` rather than leaving the
judgment open — see "Seed the CLI specification here" above. This is the
one place where the user has pre-empted the architect's step-6 call.

**Step 7 — does this need user-facing documentation? Seed: yes.** The
README's Usage section documents only the console script and describes
exit behavior loosely as "returns a nonzero exit code when validation
fails." It never distinguishes `1` from `2`, and never mentions
`python -m tiredize`. This fix makes the module invocation usable as a CI
and pre-commit gate, which is precisely the use the README's Usage
section is pitched at, so the exit-code contract is worth stating
explicitly there.

Note for whoever writes that prose: this issue refers to the invocation
as `python -m tiredize` throughout, but many systems ship only `python3`,
and the development machine this issue was scoped on is one of them —
`python -m tiredize` returns 127 there. Reader-facing documentation
should not tell people to run a command that may not exist. Tests are
unaffected because they invoke `sys.executable`.

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

### 2026-09-05T12:00:00+00:00

Author: program-manager

    Scope amended at the step-1 approval gate on the user's direction.
    Four changes, all user-decided:

    1. Errors now abort the run. A missing input document aborts like a
       configuration error, making the rule uniform (errors abort,
       findings continue). This changes `main()` and therefore the
       console script too, so this is no longer a pure propagation fix.
       The batch-validator argument for keeping the current
       continue-on-missing-document behavior was presented and declined.
    2. The exit-code contract now names the concrete finding categories
       (linter violations, markdown schema mismatches, frontmatter schema
       violations) instead of hiding them behind the word "findings," and
       states the processing semantics explicitly.
    3. `.context/specifications/cli.md` is now in scope, seeded with the
       exit-code contract only. This pre-empts the architect's step-6
       judgment; the architect still owns the document's content.
    4. The `assignee: PM` to `program-manager` schema fix is folded into
       this issue rather than split out, over the scope-discipline
       objection.

    Acceptance criteria grew from five to eight. The former criterion
    "console-script behavior is unchanged" was reworded to "the existing
    `tests/test_cli.py` suite passes without modification," because
    console-script behavior is no longer unchanged — change 1 alters it.
    Verified that no existing test pins the behavior being changed, so
    the reworded criterion is satisfiable.
