---
assignee: workflow-owner
created: 2026-06-15
knowledge: []
priority: medium
status: done
step: closeout
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
configuration file that is missing or unparseable, an unknown rule id, an
invalid rule configuration (an unknown key, a known key holding a
wrong-typed value, or a required key omitted), or an ambiguous schema.

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

- [x] `python -m tiredize` exits with exactly the value returned by
      `tiredize.cli.main()`: `0` when all paths are clean, `1` on findings
      or runtime error, `2` on usage error
- [x] `tiredize/__main__.py` propagates the return value of `main()` as
      the process exit status (e.g. `raise SystemExit(main())`)
- [x] An automated test invokes `python -m tiredize` as a subprocess and
      asserts the exit status for three cases: clean input (`0`), input
      with findings (`1`), and the usage error with no arguments (`2`)
- [x] Every test already in `tests/test_cli.py` passes unchanged, with one
      exception: `test_valid_document_passes_rules` is repaired to
      configure `maximum_length`, because criterion 9 turns its current
      `max_length` into an error. New tests may be added to that file; no
      other existing test in it may be edited or deleted
- [x] `python -m tiredize` and `tiredize` produce identical stdout and
      stderr for the same arguments
- [x] A runtime error aborts the run: given several paths where an earlier
      one is a missing input document, no later path is processed and the
      process exits `1`. Verified for both `python -m tiredize` and the
      console script
- [x] `.context/schemas/issue-frontmatter.yaml` allows
      `assignee: program-manager` in place of `PM`,
      `.context/issues/context-process-migration.md` is updated to match,
      and every file in `.context/issues/` validates clean
- [x] `.context/specifications/cli.md` exists, follows
      `templates/SPECIFICATION.md`, and documents the exit-code contract
      including the findings-continue and errors-abort semantics
- [x] An invalid rule configuration is a runtime error. All three states
      are errors: a key the rule does not accept, a key the rule accepts
      holding a value of the wrong type, and a required key omitted. Each
      prints to stderr naming the rule id and the offending key, exits
      `1`, and aborts the run per the processing semantics above. An
      omitted optional key remains legal and is not an error
- [x] Every built-in rule validates its configuration this way, and
      `.context/specifications/linter.md` documents the convention so a
      new rule author cannot omit it by accident

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

### Step 3 owns the assignee schema change

Criterion 7 requires the schema edit but no step claimed it. The
software-engineer at step 3 makes it, alongside the `__main__.py` fix,
and removes the two vocabulary skip markers in the same commit. Without
this, those skips survive to step 5 and a green suite hides an unmet
criterion.

### The assignee change is a sync, not a new decision

The upstream master copy of this schema,
`dotclaude/schemas/tiredize/issue-frontmatter.yaml`, **already lists
`program-manager` and does not list `PM` at all**. tiredize's
`.context/schemas/issue-frontmatter.yaml` is the stale copy. So criterion
7 reconciles a divergence rather than inventing a value, and the
replacement reading is correct: `PM` is removed, not kept as an alias.
The step-2 test asserting `PM` is rejected matches upstream.

Do **not** run `dotclaude distribute-schemas` to achieve this. That
command writes to a consuming repo's root `schemas/tiredize/`
(`bin/dotclaude:201-225`), not to `.context/schemas/`, so it would create
a second copy at a different path instead of updating this one. Edit
`.context/schemas/issue-frontmatter.yaml` by hand to match upstream's
`assignee` list. The two copies also differ in header comments and in the
usage path they document; leave those alone — reconciling the placement
convention is dotclaude's open `schema-placement-convention` issue, not
this one.

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

### Validating rule configuration

Criteria 9 and 10 were folded in at the gate-2 open question, against the
PM's recommendation to split them out. The user weighed the argument and
chose to fold. This roughly doubles the issue: it changes the linter
engine, not just the CLI exit-code plumbing.

**Where the key set lives.** A rule already receives its whole config
dict, so nothing forces its accepted keys onto the `Rule` dataclass and
the discovery mechanism does not change. Each rule declares its own
accepted and required keys inline and validates them as the first thing
`validate()` does. To keep the check uniform, add one shared helper
beside the existing accessors in `tiredize/linter/utils.py` — something
of the shape `validate_config(config, allowed, required, rule_id)` — and
have every rule call it. Writing the check seven times by hand was
rejected: the messages would drift between rules and a new rule author
who forgets it reintroduces the silent failure with nothing to catch it.

**Why the accessors are not enough.** `get_config_int` and its siblings
return `None` for a key that is missing *and* for one holding the wrong
type (`utils.py:20-22`), so they cannot tell the two apart. The three
error states must be distinguished before the accessors are reached,
which is why the check belongs at the top of `validate()` rather than
inside the accessors.

**Deriving required versus optional.** The governing principle is that
**enabling a rule must never be a no-op**: if a rule appears in the
configuration, it must do something. So a key is *required* when its
absence leaves the rule inert, and *optional* when the rule still does
its job without it.

Applied to the current rules: `line_length.maximum_length` is required
(`line_length.py:62-64` returns `[]` without it). `elements.disallow` and
`links.validate` are **also required** — `elements.py:24-26` and
`links.py:45-47` both return `[]` when the key is absent, so configuring
either rule without its key enables a check that checks nothing. That is
precisely the silent no-op these criteria exist to eliminate.
`line_length.exclude`, `links.timeout`, `links.headers`,
`links.valid_status_codes` and the other fallback-default keys are
optional.

Required means the key must be *present*, not that it must be truthy.
`links: {validate: false}` is legal and deliberately disables URL
checking; the key is there, so it is not the silent-typo failure mode.

This supersedes an earlier code-shape heuristic recorded here that
classified by whether a key had a fallback default. `elements.disallow`
and `links.validate` have both a default and an early return, so that
heuristic could not settle them.

**Spec consequence.** This changes the rule-module convention, so step 6
now updates `.context/specifications/linter.md` as well as authoring
`cli.md`. That is criterion 10's second half.

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

**Unknown rule-configuration keys are silently ignored.** Raised by the
qa-engineer at step 2 as an open-question action tag. Every accessor in
`tiredize/linter/utils.py` (`get_config_int`, `get_config_str`,
`get_config_bool`, `get_config_dict`, `get_config_list`) returns `None`
for a key that is missing or of the wrong type, and every rule reads
`None` as "not configured" and returns no findings. A typo in any rule's
configuration therefore switches that rule off across the whole tool,
silently. `tests/test_cli.py::test_valid_document_passes_rules` is a live
instance: it configures `max_length` where `line_length.py:62` reads
`maximum_length`, so the rule never runs and the test asserts a clean
document against a check that did not execute.

**Resolved.** The user folded it into this issue as criteria 9 and 10
rather than splitting it out, and ruled that all three key states are
errors — unknown key, wrong-typed value, and omitted required key. The
design is recorded under "Validating rule configuration" in Design
Decisions. Criterion 4 was amended to permit repairing
`test_valid_document_passes_rules`, which criterion 9 would otherwise
break while criterion 4 forbade touching it.

Step 2 is re-entered to author acceptance tests for criteria 9 and 10
before implementation begins.

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

### 2026-09-05T13:00:00+00:00

Author: program-manager

    Approval gate 1 passed. The user approved the eight acceptance
    criteria and the exit-code contract as written, including the
    abort-on-runtime-error change to `main()` and its knock-on effect on
    the console script.

    Routing to step 2, acceptance test design. The qa-engineer writes
    failing black-box tests against the Public Contract section before
    any implementation exists. Note for that step: criterion 6 (a runtime
    error aborts the run) asserts behavior that does not exist yet and
    must be written to fail, not to characterize what the code does
    today.

### 2026-09-05T14:00:00+00:00

Author: qa-engineer/software-engineering/testing

    Acceptance test design complete. All sections of the issue are
    present and the Public Contract is specified well enough to test
    against; no blocking gap was found.

    Delivered `tests/test_main_module.py` — 23 black-box tests derived
    from the Public Contract, in three classes. Every test spawns a
    subprocess (`sys.executable -m tiredize`, or the console script
    located with `shutil.which`) with `cwd` at the repository root, so
    nothing in the suite depends on how `tiredize/__main__.py` is
    written. `TestModuleExecution` is deliberately not used; that name
    is reserved for the step-3 white-box tests in the same file.

    Classes:

      - `TestExitStatus` — process exit status and processing
        semantics (criteria 1, 2, 3, 6).
      - `TestStreamParity` — stdout/stderr/exit-status parity between
        the two entry points (criterion 5).
      - `TestIssueAssigneeVocabulary` — the assignee vocabulary, driven
        through the console script against the project's own schemas
        (criterion 7).

    Three classes rather than the two the routing suggested: the
    vocabulary tests validate configuration files, not the `-m` entry
    point, and folding them into `TestExitStatus` would misdescribe
    them. Test methods are ordered narratively under banner comments,
    matching `tests/validators/test_frontmatter_schema.py`, rather than
    alphabetized — alphabetizing would break the reading order.

    Coverage by acceptance criterion:

    1. `-m` exits with exactly what `main()` returns.
       `test_clean_document_exits_zero`,
       `test_several_clean_documents_exit_zero` (0);
       `test_markdown_schema_finding_exits_one`,
       `test_linter_rule_finding_exits_one`,
       `test_frontmatter_schema_finding_exits_one`,
       `test_findings_do_not_stop_the_run`,
       `test_missing_configuration_file_exits_one`,
       `test_unknown_rule_id_exits_one`,
       `test_missing_document_exits_one` (1);
       `test_no_arguments_exits_two`,
       `test_paths_without_configuration_exit_two`,
       `test_configuration_without_paths_exits_two`,
       `test_unknown_flag_exits_two` (2). All three finding categories
       named in the contract get their own case, as do four runtime
       error kinds and all three usage-error permutations.
       `test_unknown_flag_exits_two` pins the argparse path that is
       already correct and must stay correct.

    2. `__main__.py` propagates `main()`'s return value. No black-box
       test asserts the source idiom — that is an internal detail and
       out of bounds for this tier. Its entire observable consequence
       is criterion 1, which is fully covered above. The
       `raise SystemExit(main())` preference is a code-review check at
       step 4.

    3. A subprocess test asserts 0, 1 and 2. Satisfied by
       `test_clean_document_exits_zero`,
       `test_markdown_schema_finding_exits_one` and
       `test_no_arguments_exits_two` respectively.

    4. `tests/test_cli.py` passes unchanged. No new test can assert
       this; it is verified by running the suite and by `git diff`
       showing that file untouched. Both confirmed: the full suite is
       729 passed / 68 skipped, and `tests/test_cli.py` was not
       modified. No test was added to it — everything fits in
       `tests/test_main_module.py`.

    5. Identical stdout and stderr for the same arguments.
       `test_parity_for_clean_document`, `test_parity_for_findings`,
       `test_parity_for_runtime_error`, `test_parity_for_usage_error`,
       `test_parity_for_non_ascii_findings`. Each runs both entry
       points with one argument list and compares all three observable
       outputs. The non-ASCII case (emoji heading, accented text) is
       there because the finding message carries computed line and
       column offsets into user text.

    6. A runtime error aborts the run.
       `test_module_aborts_after_missing_document` and
       `test_console_script_aborts_after_missing_document`. Both pass a
       missing document followed by a clean one and assert the later
       path is absent from stdout. Written against the contract, not
       against today's behavior, per the routing note.

    7. Assignee vocabulary. `test_program_manager_is_allowed`,
       `test_pm_is_no_longer_allowed`,
       `test_every_issue_file_validates_clean`. These run the console
       script because that is what CI and the pre-commit hook use and
       because its exit status is already correct today, so the
       assertions are meaningful before the `-m` fix lands.

    8. `.context/specifications/cli.md`. No automated test. Existence
       and content are checkable but conformance to
       `templates/SPECIFICATION.md` is a structural-judgment call with
       no machine-readable schema in this repository, so a test would
       assert only the cheap half and give false assurance. Also, the
       document is authored by the technical-architect at step 6, so a
       test for it would have to stay skipped through steps 3 to 5,
       against the convention that step 3 clears every skip. Verified
       instead by inspection at step 5 acceptance verification and at
       step 6 against the template.

    Criterion needing clarification — criterion 7. "Allows
    `assignee: program-manager` in place of `PM`" is read as
    replacement, not addition, so `test_pm_is_no_longer_allowed`
    asserts `PM` is rejected. The Design Decisions rationale supports
    that reading: `PM` is called "the lone exception" among values that
    match function filenames, and removing it is what makes the
    vocabulary uniform. Flagging it rather than assuming: if the user
    intends `PM` to remain valid as a legacy alias, that one test
    should be dropped at the approval gate.

    Pre-skip failure evidence. The suite was first run with no skip
    markers: 5 passed, 18 failed, and every failure was an assertion
    failure with observed-versus-expected values — no import error, no
    missing fixture, no wrong cwd, no `FileNotFoundError` on the
    console script.

      - The eleven `-m` exit-status tests and both abort tests failed
        as `assert 0 == 1` or `assert 0 == 2`: the module printed the
        right findings or the right error to the right stream and then
        exited 0 anyway. Example: the unknown-rule case produced
        `error: Unknown rule id: the_rule_of_cool` on stderr with
        returncode 0.
      - `test_console_script_aborts_after_missing_document` failed
        differently, and this is the evidence for criterion 6 being a
        genuine behavior change rather than a propagation artifact. The
        console script already exits 1, so it failed on the abort
        assertion instead: `assert '.../nap_time.md' not in '...'`,
        because `nap_time.md: no issues found.` was still printed after
        `error: Path does not exist: .../phantom_thread.md`.
      - The four failing parity tests failed on the exit status pair —
        e.g. `assert 0 == 1` where 0 is the module and 1 the console
        script. stdout and stderr already matched in every case, so
        parity fails today only on exit status.
      - `test_program_manager_is_allowed` failed `assert 1 == 0`, with
        `[schema.frontmatter.value_not_allowed] Field 'assignee' value
        'program-manager' is not allowed`.
        `test_pm_is_no_longer_allowed` failed `assert 0 == 1` — `PM`
        still validates clean.

    Five tests passed unskipped and stay unskipped:
    `test_clean_document_exits_zero`,
    `test_several_clean_documents_exit_zero`,
    `test_unknown_flag_exits_two`, `test_parity_for_clean_document`,
    `test_every_issue_file_validates_clean`. The last one passes today
    and is a deliberate guard: swapping the schema's allowed value
    without updating `context-process-migration.md` will break it.

    Skip markers step 3 must remove. All 18 carry
    `@pytest.mark.skip(reason=PENDING)`, where `PENDING` names this
    issue file and says the skip is removed when the fix lands. This is
    the mechanism the testing knowledge prescribes for a test that
    asserts the contract against code that does not meet it yet; no
    test was weakened and the pre-commit hook was not bypassed.

      - `TestExitStatus`: `test_markdown_schema_finding_exits_one`,
        `test_linter_rule_finding_exits_one`,
        `test_frontmatter_schema_finding_exits_one`,
        `test_findings_do_not_stop_the_run`,
        `test_missing_configuration_file_exits_one`,
        `test_unknown_rule_id_exits_one`,
        `test_missing_document_exits_one`,
        `test_no_arguments_exits_two`,
        `test_paths_without_configuration_exit_two`,
        `test_configuration_without_paths_exits_two`,
        `test_module_aborts_after_missing_document`,
        `test_console_script_aborts_after_missing_document`.
      - `TestStreamParity`: `test_parity_for_findings`,
        `test_parity_for_runtime_error`,
        `test_parity_for_usage_error`,
        `test_parity_for_non_ascii_findings`.
      - `TestIssueAssigneeVocabulary`:
        `test_program_manager_is_allowed`,
        `test_pm_is_no_longer_allowed`.

    Note for step 3: the last two come off only once the schema fix in
    criterion 7 is made. If that fix is not part of step 3's work, the
    step should say so rather than leave the skips unexplained — no
    later step is currently assigned to it.

    Observations for triage, outside the eight criteria and not acted
    on:

      - `tests/test_cli.py` configures the `line_length` rule with
        `max_length`, but the rule reads `maximum_length` and returns
        no results when the key is absent. `test_valid_document_passes
        _rules` therefore asserts "no issues found" against a rule that
        never ran. The test is not wrong, but it does not test what its
        name suggests. Out of scope here, and criterion 4 forbids
        editing it.
      - The installed console script is an editable install pointing at
        this working tree, which is what makes the parity and vocabulary
        tests meaningful. On a machine where `tiredize` resolves to a
        different copy, those tests would compare two different
        versions. `_console_script` skips when the script is absent but
        cannot detect a stale one. Worth a note in contributor
        documentation eventually.

    Step 2 is an approval gate. Stopping here for the user to confirm
    the suite captures their intent, in particular the criterion 7
    reading above, before any implementation begins.

### 2026-09-05T15:00:00+00:00

Author: qa-engineer/software-engineering/testing

    Two follow-ups from the user, recorded here so neither is lost.

    Criterion 7 reading confirmed. The user confirms that
    `program-manager` replaces `PM` rather than joining it, and that
    `PM` is to be rejected. `test_pm_is_no_longer_allowed` already
    asserts exactly that and needs no change. The clarification flagged
    in the previous comment is resolved; no other test is affected.

    Unknown rule configuration keys should be a runtime error. The user
    wants an unrecognized setting inside a rule's configuration block to
    raise an error and exit `1`, rather than being silently ignored.
    This came out of the `max_length` versus `maximum_length`
    observation above, and it is broader than that one rule: every
    accessor in `tiredize/linter/utils.py` (`get_config_int`,
    `get_config_str`, `get_config_bool`, `get_config_dict`,
    `get_config_list`) returns `None` when a key is absent or the wrong
    type, and every rule treats `None` as "not configured" and no-ops.
    So today a typo in any rule's configuration silently disables that
    rule everywhere, not only in `line_length`. A misspelled key and a
    correctly-spelled key with the wrong value type are two distinct
    cases and probably want distinguishing.

    This is new behavior, not covered by any of the eight acceptance
    criteria, and it changes the linter engine rather than the exit-code
    plumbing this issue is about. The qa-engineer does not write tests
    for criteria that do not exist yet and does not edit the Acceptance
    Criteria section, so no test has been added for it. It needs a
    scoping decision first: whether it is a ninth criterion on this
    issue or a separate issue. It fits the existing exit-code contract
    cleanly either way — it is a configuration error, which the contract
    already classifies as a runtime error, so it would exit `1` and,
    after this issue lands, abort the run.

    Action: @program-manager — open question: scope the unknown-rule-
    configuration-key error. Decide whether it becomes a ninth
    acceptance criterion here or a separate issue, and specify the
    intended behavior (which key states are errors, whether a wrong-type
    value is distinguished from an unknown key, and what the message
    says). Once scoped, step 2 can be re-entered to add the acceptance
    tests for it. Stopping rather than assuming.

### 2026-09-05T16:00:00+00:00

Author: qa-engineer/software-engineering/testing

    Step 2 re-entered for criteria 9 and 10 only. The 23 tests written
    at the first pass are untouched — no test was edited, renamed,
    reordered or deleted, and no existing skip marker was removed.

    Delivered one new class in `tests/test_main_module.py`,
    `TestRuleConfigurationValidation`: 10 test functions, 20 pytest
    items (two are parametrized over the six built-in rules). File
    total is now 33 test functions / 43 items. Two new module-level
    helpers were added alongside the existing ones — `_rule_modules()`
    and `_write_rule_config()` — plus the constants `RULES_PACKAGE`,
    `BASELINE_RULE_CONFIGS` and `WRONG_TYPED_RULE_CONFIGS`.

    Entry point. These drive the `tiredize` console script, not
    `python -m tiredize`, following the `TestIssueAssigneeVocabulary`
    precedent. Criteria 9 and 10 are linter-engine behaviour, not `-m`
    plumbing. Driving them through `-m` would make every one of them
    fail today for two independent reasons — the absent configuration
    validation *and* the discarded exit code — so a failure would not
    be attributable to the behaviour under test, and a regression in
    one defect could be masked by the other. The console script's exit
    status is already correct today, so each failure here is
    attributable to configuration validation alone. That both entry
    points report these errors identically is already covered by
    `TestStreamParity`, which asserts stdout, stderr and exit-status
    parity for a runtime error.

    Coverage by acceptance criterion:

    9. An invalid rule configuration is a runtime error. All four
       states named in the criterion get a case, on `line_length`
       because its required-versus-optional split is unambiguous under
       the derivation rule in Design Decisions — `maximum_length` is
       read and the rule produces nothing when it is absent
       (required); `exclude` has a fallback default (optional).

         - `test_unknown_key_is_an_error` — a key the rule does not
           accept (`max_length`, the real typo from `test_cli.py`).
         - `test_required_key_with_wrong_type_is_an_error` —
           `maximum_length` holding a string.
         - `test_optional_key_with_wrong_type_is_an_error` —
           `exclude` holding a bare string where a list is wanted.
           Optional does not mean unchecked.
         - `test_required_key_omitted_is_an_error` — `maximum_length`
           absent, `exclude` present so the block is still a mapping.
         - `test_unicode_required_key_omitted_is_an_error` — the same
           state on a second rule whose required key is equally
           unambiguous (`unicode` reads `allowed` and produces nothing
           when it is absent).
         - `test_omitted_optional_key_is_not_an_error` — the negative
           case. An omitted optional key stays legal and exits `0`.
         - `test_invalid_configuration_aborts_the_run` — two paths,
           the bad configuration, and assertions that the later path
           never appears in stdout and that no `no issues found` line
           is printed at all.

       Every error case asserts all three halves of the observable
       contract: exit status `1`, the rule id in stderr, and the
       offending key in stderr.

    10. Every built-in rule validates its configuration this way.

         - `test_unknown_key_is_an_error_for_every_rule` —
           parametrized over all six non-private rule modules
           (`elements`, `line_length`, `links`, `tabs`,
           `trailing_whitespace`, `unicode`). Each case starts from a
           valid baseline configuration for that rule and appends one
           key no rule accepts, so the appended key is the only fault
           and the case holds whether the baseline keys are required
           or optional.
         - `test_wrong_typed_value_is_an_error_for_every_rule` —
           parametrized over the same six. Each takes a key the rule
           does accept and gives it a value of the wrong type. Also
           independent of the required-versus-optional reading.
         - `test_every_rule_module_has_a_configuration_case` — the
           guard. It reads the non-private `*.py` stems out of
           `tiredize/linter/rules/` and asserts that set equals the
           key set of both parametrization maps. Adding a rule module
           without adding it to both maps fails this test, which is
           what gives "a new rule author cannot omit it by accident"
           teeth on the code half of the criterion.

       The required-key-omitted state is deliberately *not*
       parametrized over all six. For `tabs`, `trailing_whitespace`,
       `elements` and `links` the derivation rule does not settle
       whether the key is required — `tabs.allowed` and
       `trailing_whitespace.allowed` are read with no fatal branch;
       `elements.disallow` has an `or []` fallback but then produces
       nothing when empty; `links.validate` cannot distinguish an
       absent key from `false`. Pinning a reading there would be
       inventing policy, which Design Decisions forbids. The fixtures
       above are built to hold under either reading instead.

       Criterion 10's second half — that
       `.context/specifications/linter.md` documents the convention —
       is not machine-assertable, the same category as criterion 8.
       Whether prose adequately teaches a convention is a judgement
       call with no machine-readable schema in this repository, and
       the document is authored by the technical-architect at step 6,
       so any test for it would have to stay skipped through steps 3
       to 5 against the convention that step 3 clears every skip. It
       will be verified by inspection twice: at step 6, by the
       technical-architect, against `templates/SPECIFICATION.md` and
       against the "Rule Module Convention" and "Configuration
       Helpers" sections that must now name the validation
       requirement; and at step 5 acceptance verification, by reading
       the section and confirming a new rule author following it alone
       would write the check. No hollow test was invented for it.

    Pre-skip failure evidence. The class was first run with no skip
    markers: 18 failed, 2 passed. Every failure was an assertion
    failure with observed-versus-expected values — no import error, no
    setup error, no missing fixture, no `FileNotFoundError` on the
    console script.

      - All 18 failed identically on the first assertion,
        `assert result.returncode == 1` reported as `assert 0 == 1`,
        with `stderr=''` and stdout carrying
        `.../nap_time.md: no issues found.` — the invalid
        configuration was accepted in silence and the rule no-opped,
        which is precisely the defect criteria 9 and 10 exist to
        close.
      - `test_invalid_configuration_aborts_the_run` failed the same
        way and its stdout showed both paths reported —
        `.../nap_time.md: no issues found.` followed by
        `.../second_nap.md: no issues found.` — so the abort
        assertions further down would have failed too had the exit
        status matched.
      - The two passing tests are
        `test_omitted_optional_key_is_not_an_error` and
        `test_every_rule_module_has_a_configuration_case`. Both are
        meaningful guards rather than accidental passes, so both are
        left unskipped: the first fails if validation over-reaches and
        demands an optional key; the second fails if a rule module is
        added without a validation case.

    Skip markers step 3 must remove — eight functions, 18 items, all
    carrying `@pytest.mark.skip(reason=PENDING)`:
    `test_unknown_key_is_an_error`,
    `test_required_key_with_wrong_type_is_an_error`,
    `test_optional_key_with_wrong_type_is_an_error`,
    `test_required_key_omitted_is_an_error`,
    `test_unicode_required_key_omitted_is_an_error`,
    `test_invalid_configuration_aborts_the_run`,
    `test_unknown_key_is_an_error_for_every_rule`,
    `test_wrong_typed_value_is_an_error_for_every_rule`. No test was
    weakened to make it pass and the pre-commit hook was not bypassed.

    Suite state: 731 passed / 86 skipped, up from 729 / 68.
    `flake8 tiredize tests` is clean. `tiredize/` is byte-for-byte
    unchanged — `git diff --stat 7380a85 HEAD -- tiredize/` is empty
    and the working tree shows no modification under `tiredize/`.
    `tests/test_cli.py` was not touched.

    Observations for triage, outside criteria 9 and 10 and not acted
    on:

      - The error message wording is not pinned by these tests beyond
        "names the rule id and the offending key", which is all the
        criterion promises. If the messages are meant to be uniform
        across rules — the stated reason for the shared helper — that
        uniformity is a code-review check at step 4, not something
        these tests assert.
      - `line_length.exclude` and `unicode.exclude` accept element
        names and raise `ValueError` on an unknown one, and
        `links.valid_status_codes` validates its entries. Those are
        value-level checks that already produce a runtime error today.
        Criterion 9 is about key-level validation, so the two layers
        will coexist; whoever implements the shared helper should be
        careful not to duplicate or contradict the existing
        element-name and status-code messages.
      - The `elements` rule's `disallow` and the `links` rule's
        `validate` read as enable-toggles rather than required keys.
        If the implementer's reading differs from that, nothing in
        this suite breaks — the fixtures were built to be neutral —
        but it is worth a deliberate call at step 3 rather than an
        accidental one.

### 2026-09-05T18:00:00+00:00

Author: program-manager

    Approval gate 2 passed. The user approved the 33 acceptance tests as
    capturing intent, including the four items the qa-engineer raised:
    the console-script entry point for `TestRuleConfigurationValidation`,
    wrong-typed optional keys being errors, substring-only stderr
    assertions, and the required-versus-optional classification now
    settled under "Validating rule configuration".

    Routing to step 3, implementation. Two of the three approval gates
    are now behind us; the next scheduled stop is gate 3 at closeout.
    Steps 3 through 10 run without user involvement unless an agent
    raises an open question, a disputed edit, or a review loop hits its
    iteration cap.

    Reminder for step 3, all of it already recorded above: clear every
    one of the 26 skip markers, repair `test_valid_document_passes_rules`
    (criterion 4 carves out that one test by name), and treat
    `elements.disallow` and `links.validate` as required keys.

### 2026-09-05T19:00:00+00:00

Author: software-engineer/software-engineering/git,python,testing

    Implementation complete. All sections of the issue are present and
    complete per `templates/ISSUE.md`; nothing blocked the step and no
    open question was raised.

    Pre-implementation check. The 33 acceptance tests were run with
    their skip markers stripped: 36 failed / 7 passed, matching the
    qa-engineer's recorded evidence exactly (18 failed / 5 passed for
    the first batch, 18 failed / 2 passed for the second). Every
    failure was an assertion failure with observed-versus-expected
    values — no import error, no setup error. Two signatures were
    spot-checked against the record and matched:
    `test_console_script_aborts_after_missing_document` failing on the
    abort assertion rather than the exit status, and
    `test_program_manager_is_allowed` failing `assert 1 == 0` with
    `value_not_allowed`.

    Three commits, one per group of criteria.

    Criterion 7 — assignee vocabulary. `.context/schemas/issue-
    frontmatter.yaml` was edited by hand to match upstream's
    `assignee` list: `program-manager` replaces `PM`, which is removed
    rather than kept as an alias, and the order matches upstream too.
    `dotclaude distribute-schemas` was not run. Header comments and
    the documented usage path were left alone.
    `.context/issues/context-process-migration.md` carried the only
    `assignee: PM` in the repository and moved with it. Its prose
    mention of "PM-led maintenance" at line 78 is not frontmatter and
    was left alone.

    Criteria 1, 2, 3, 5, 6 — exit-code propagation and abort
    semantics. `tiredize/__main__.py` now raises `SystemExit(main())`,
    the preferred idiom; no deviation was needed. `main()`'s
    `FileNotFoundError` handler returns 1 instead of continuing, so
    all runtime errors abort. `main()` gained a docstring stating the
    three return values and the findings-continue/errors-abort rule.

    Criteria 9, 10 — rule configuration validation.
    `validate_config(config, allowed, required, rule_id)` sits beside
    the accessors in `tiredize/linter/utils.py`. `allowed` maps each
    key to a type name from a five-entry vocabulary (`bool`, `dict`,
    `int`, `list`, `str`) whose predicates mirror the matching
    `get_config_*` accessor — so a value the helper accepts is one the
    accessor will return rather than treat as absent, including
    rejecting `bool` where `int` is declared. Faults are reported in a
    fixed order: unknown keys, then omitted required keys, then
    wrong-typed values. Unknown keys come first because a typo is both
    the likeliest fault and the one that makes the others misleading —
    a misspelled required key reads as an omission until its real name
    is pointed out. Every message names the rule id and the offending
    key, and the unknown-key message also lists the accepted keys.

    Each rule declares `_RULE_ID`, `_ALLOWED_KEYS` and
    `_REQUIRED_KEYS` inline and calls the helper as the first
    statement in `validate()`. The `Rule` dataclass and rule discovery
    are untouched.

    Required-versus-optional, applying the settled principle that a
    key is required when its absence leaves the rule inert:

      - Required: `line_length.maximum_length`, `elements.disallow`,
        `links.validate`, `unicode.allowed`. Each rule returns `[]`
        outright when its key is absent.
      - Optional: `tabs.allowed` and `trailing_whitespace.allowed`.
        The qa-engineer flagged these as unsettled by the earlier
        code-shape heuristic; the principle settles them. With the key
        absent both rules still forbid what they exist to forbid, so
        enabling them is never a no-op. This was a deliberate call,
        not an accidental one, per the note at the end of the step-2
        comment.
      - Also optional: `line_length.exclude`, `unicode.exclude`,
        `links.exclude`, `links.headers`, `links.timeout`,
        `links.valid_status_codes`.

    Required means present, not truthy: `links: {validate: false}` is
    legal.

    Coexistence with the existing value-level checks. Key-level
    validation runs first and none of the existing `ValueError`
    messages were changed or duplicated — `line_length.exclude` and
    `unicode.exclude` element names, `elements.disallow` element
    names, and `links.valid_status_codes` entries are all still
    reported by the rules' own wording. Four tests pin the ordering
    (an unknown key alongside a bad element name reports the unknown
    key) and four more pin that a list holding a non-string still
    reaches the value-level message.

    Now-unreachable guards removed: the `if maximum_length is None`,
    `if allowed is None` and `get_config_list(...) or []` fallbacks in
    `line_length`, `unicode` and `elements` that the helper makes
    impossible to hit. `elements`' empty-list early return stays —
    `disallow: []` is present, legal and means "allow everything".

    White-box tests added, from the coverage and input-boundary
    audits:

      - `tests/test_main_module.py::TestModuleExecution` — six
        in-process tests driving the module body through
        `runpy.run_module("tiredize", run_name="__main__")` with
        `sys.argv` patched, asserting on `SystemExit.code`. Covers
        the three returned codes, the argparse `SystemExit` that
        unwinds through the statement rather than being constructed
        by it, and re-execution in one interpreter.
      - `tests/linter/test_utils.py` — 24 tests for
        `validate_config`: the three error states, ordering when
        faults coexist, one wrong type per declared type, bool/int
        confusion in both directions, `None` values, empty
        collections and empty strings, non-ASCII keys and values,
        no-mutation of any of its three inputs, and idempotency.
      - `tests/linter/rules/test_loader.py` — four parametrized
        guards over every discovered built-in rule: the declaration
        exists and `_RULE_ID` matches the id the loader derives from
        the module name, the minimal config is accepted, an unknown
        key is rejected, and dropping any required key is rejected.
        This is the code half of "a new rule author cannot omit it by
        accident": a rule module added without the declaration fails
        collection or the first guard.
      - Per-rule configuration sections in all six rule test files.
      - `tests/test_cli.py::test_missing_document_aborts_remaining_
        paths` — the abort, in-process.

    Existing tests changed. Seven asserted the silent-no-op behaviour
    criteria 9 and 10 remove, and now assert the error instead:
    `test_engine.py::test_run_linter_undefined_rule` (renamed
    `..._undefined_rule_key_raises`),
    `test_elements.py::test_missing_disallow_returns_empty`,
    `test_links.py::test_validate_missing_returns_empty`,
    `test_unicode.py::test_missing_allowed_returns_empty` and
    `test_allowed_none_returns_empty`, and the
    `test_config_allowed_wrong_type` cases in `test_tabs.py` and
    `test_trailing_whitespace.py`. These are not acceptance tests and
    are not in `tests/test_cli.py`, so no criterion protected them;
    leaving them would have meant the suite asserting both the old and
    the new contract at once. `tests/test_cli.py::test_valid_document
    _passes_rules` was repaired to `maximum_length` per criterion 4;
    no other test in that file was edited or deleted.

    The `PENDING` constant in `tests/test_main_module.py` was removed
    along with the last skip marker that referenced it. It was
    scaffolding for the skips only, and its comment ("They fail until
    the fix lands") would have been actively wrong left behind. No
    test was touched.

    Definition of Done. `flake8 tiredize tests` is clean. Full suite:
    844 passed / 50 skipped / 0 failed. All 50 remaining skips are the
    pre-existing `gfm-parity` skips in the markdown parser tests;
    `tests/test_main_module.py` has zero skip markers, verified by
    grep. Coverage for changed source files: `tiredize/__main__.py`
    100% (was 0%), `tiredize/linter/utils.py` 100%,
    `tiredize/linter/rules/{tabs,trailing_whitespace,links}.py` 100%,
    `unicode.py` 98%, `elements.py` 97%, `line_length.py` 95%,
    `cli.py` 98%. Every uncovered line is a pre-existing gap in code
    this issue did not touch: the range-merge branches in
    `line_length.py` and `unicode.py`, the zero-length-element
    `continue` in `elements.py`, the empty-YAML `return {}` and the
    `if __name__ == "__main__"` guard in `cli.py`, and the
    `isinstance(rule, Rule)` check in `engine.py` that a comment in
    `test_engine.py` already documents as unreachable. No new
    uncovered line was introduced.

    Still open, and not this step's to close. Criterion 8
    (`.context/specifications/cli.md`) and the second half of
    criterion 10 (`.context/specifications/linter.md` documenting the
    rule-module convention) are authored by the technical-architect at
    step 6. Nothing was written to `.context/specifications/`.

    Observations for triage, outside the ten criteria and not acted
    on:

      - The README's rule reference at lines 182-300 documents the
        configuration keys correctly, so no example there breaks. It
        does not yet say that an unrecognized or wrong-typed key is
        now an error, or which keys are required. Worth a line when
        step 8 revisits the Usage section.
      - `validate_config` does not check that `config` is a mapping.
        `run_linter` already raises for that at `engine.py:57-60` and
        adding a second message for the same condition would risk the
        contradiction criterion 9 warns about, so the engine keeps
        ownership of it.
      - The type vocabulary is coarse: `list` and `dict` are not
        checked element-wise. Every rule that cares already checks
        its own entries at value level, so nothing is unguarded, but
        a future rule author could declare `list` and forget the
        inner check.

### 2026-09-05T20:00:00+00:00

Author: software-engineer/software-engineering/code-review,python,testing

    Code and test review complete. Verdict: two findings, both
    documentation-level. The implementation and the tests are
    otherwise sound; nothing in the source needs correcting.

    All sections of the issue are present and complete per
    `templates/ISSUE.md`, and nothing blocked the step.

    Independent verification, not taken on the implementation's word.
    `flake8 tiredize tests` is clean. Full suite: 844 passed / 50
    skipped / 0 failed. Coverage of the changed files matches the
    step-3 report and every uncovered line is a pre-existing gap in
    code this issue did not touch; no new uncovered line was
    introduced. The exit-status, parity and abort behaviour was also
    exercised by hand against both entry points.

    Findings by category:

      - Unused parameters or dead code -- one, finding 2 below.
      - Duplicate or redundant logic -- none found.
      - Missing input validation -- none found.
      - Inconsistencies between parallel code paths -- none found.
      - Silent acceptance of invalid input -- none found.
      - Reachable bugs or error-handling gaps -- none found.
      - Contract violations -- none found.
      - Spec fidelity gaps -- one, finding 1 below.

    Finding 1 -- spec fidelity. `README.md:237`, in the `unicode`
    rule's option table, says of `allowed`: "Omitting this option
    disables the rule." Criterion 9 makes that omission a runtime
    error: `error: Rule 'unicode': required configuration key
    'allowed' is missing.`, exit 1, run aborted. The README therefore
    documents behaviour the code no longer has, and a reader
    following it writes a configuration that now hard-fails.
    Correction: replace that sentence with one saying `allowed` is
    required. The step-3 comment flagged the README as *incomplete*
    on this subject; this sentence is the one place it is *wrong*. If
    the PM would rather it land with the rest of the README prose at
    step 8, that is a legitimate routing call -- but it should not be
    left to chance, because the step-7 seed points step 8 at the
    Usage section, not at the rule reference at lines 182-300.

    Finding 2 -- dead code, minor.
    `tests/linter/rules/test_unicode.py:13-15` still carries the
    `Config gating` banner, but the two tests that lived under it
    were replaced by the `Configuration validation (key level)`
    section immediately below, so the banner now heads an empty
    section. Correction: delete lines 13-15. The equivalent banners
    in `test_elements.py`, `test_links.py`, `test_tabs.py` and
    `test_trailing_whitespace.py` still have tests under them and are
    correct as they stand.

    Action: @program-manager -- request for edit

    Checked and found correct, recorded so the next pass does not
    re-review them:

      - Criterion 4. `git diff main..HEAD -- tests/test_cli.py` shows
        exactly two hunks: `max_length` to `maximum_length` in
        `test_valid_document_passes_rules`, and one added test. No
        other existing test in that file was edited or deleted.
      - The seven changed tests outside `tests/test_cli.py`. Each was
        genuinely forced by the new contract, and each asserts
        strictly more than the test it replaced -- the raise, the
        rule id and the offending key, where the old test asserted
        only `== []`. None was weakened to pass. The two tests that
        pin the *optional* reading, `test_config_missing_allowed_key`
        in `test_tabs.py` and `test_trailing_whitespace.py`, were
        correctly left untouched, so the classification is still
        pinned from both directions.
      - The `PENDING` removal. `git diff 3cbaeb7..HEAD --
        tests/test_main_module.py` shows only the constant block, the
        26 `@pytest.mark.skip(reason=PENDING)` decorators, one added
        import (`runpy`), and the appended white-box section. No
        step-2 test body, name, order or assertion changed. This is
        scaffolding removal, not an alteration of the acceptance
        tier.
      - `tabs.allowed` and `trailing_whitespace.allowed` classified
        optional. Correct under the settled principle. With the key
        absent `get_config_bool` returns `None`, both rules take the
        `not allowed` branch, and both still flag what they exist to
        flag -- enabling either is never a no-op. `unicode.allowed`
        is correctly required by the same test: absent, `allowed ==
        in_excluded` is never true and the rule inspects nothing. A
        typo such as `alowed` is still caught, as an unknown key.
      - Message uniformity. All three key-level messages are
        constructed in `validate_config` alone, so no rule can drift
        from another. Each names the rule id and the offending key,
        and each reaches stderr through `cli.py`'s `error: {exc}`.
        Verified by running all three states through the CLI.
      - Coexistence with the value-level checks. `validate_config` is
        the first statement of every `validate()`, and the existing
        `ValueError` texts for element names in `exclude` and
        `disallow` and for `valid_status_codes` entries are unchanged
        and still reachable. Four ordering tests and four
        reach-through tests pin both halves.
      - Abort semantics. Every runtime-error path in `main()` now
        returns immediately; findings still accumulate `exit_code`
        and continue to the next path; argparse still raises
        `SystemExit(2)` from inside `main()` and is pinned by
        `test_unknown_flag_exits_two` and
        `test_module_body_propagates_argparse_exit`.
      - `raise SystemExit(main())` in `tiredize/__main__.py`,
        matching the idiom at the bottom of `cli.py`.
      - Criterion 7, re-verified by hand: every file in
        `.context/issues/` validates clean against the project's own
        schemas.
      - Input boundary audit on `validate_config`. `None` values,
        bool-versus-int confusion in both directions, empty
        collections, empty strings, non-ASCII keys and values,
        no-mutation and idempotency are all covered in
        `tests/linter/test_utils.py`. Non-string YAML keys are
        handled correctly (reported as unknown keys) though not
        directly tested.

    Observations for triage, outside the ten criteria and not acted
    on:

      - A rule whose entire configuration block is null --
        `line_length:` with nothing under it -- is reported by the
        engine as `Invalid configuration for rule line_length: None`
        rather than by the new helper, so the message names the rule
        but not the required key. This is pre-existing behaviour that
        the diff does not change, the run still aborts with exit 1 on
        stderr, and step 3 recorded a deliberate decision to leave
        the non-mapping case with the engine. Noted only because it
        is the likeliest real-world shape of "a required key omitted"
        for a single-key rule.
      - `validate_config`'s type vocabulary declares `str`, which no
        built-in rule uses, and its "This rule accepts no
        configuration keys" branch cannot fire for a built-in because
        `test_loader.py` asserts every rule declares at least one
        key. Both belong to the helper's contract for future and
        custom rules and are directly covered in
        `tests/linter/test_utils.py`, so neither is dead in the sense
        this review looks for.

    Criterion 8 and the second half of criterion 10 are the
    technical-architect's at step 6 and were not reviewed.

### 2026-09-05T20:00:00+00:00

Author: program-manager

    Step 4 raised one edit request covering two findings. They route to
    two different steps, so the request is split rather than sent whole
    to step 3.

    Finding 2 — the orphaned `Config gating` banner at
    `tests/linter/rules/test_unicode.py:13-15` — routes back to step 3,
    implementation, revision mode. It is test scaffolding left behind by
    step 3's own edit and is the software-engineer's to remove.

    Finding 1 — `README.md:237` telling readers that omitting
    `unicode.allowed` disables the rule, which criterion 9 turns into a
    runtime error — is deferred to step 8, user documentation. Three
    reasons. The README is user-facing prose, which the workflow assigns
    to the ghostwriter, not the software-engineer; the reviewer named
    step 8 as a legitimate destination rather than disputing it; and the
    change that made the sentence wrong is a configuration change, which
    step 8's remit explicitly covers. Deferring it costs nothing because
    the documentation track has not run yet.

    Two consequences to carry forward, recorded here so neither is lost:

      - The step-7 documentation seed points step 8 at the README's
        Usage section only. Finding 1 lives in the rule reference at
        lines 182-300, which that seed does not name. Step 8 must cover
        both. Step 3's own step-3 comment flagged the same section as
        incomplete on this subject; finding 1 is the one place it is
        actively wrong, so the two overlap and step 8 should treat them
        together.
      - The documentation track is conditional on the technical-
        architect's decision at step 7. If that decision comes back
        "no documentation required", finding 1 does not disappear — it
        becomes an open item with no home, and the architect is asked to
        say where it goes rather than leaving it unrouted.

    Neither finding touches `tiredize/`. The reviewer's verdict on the
    source and the tests was clean, including the three items the
    routing asked it to check specifically: the seven changed tests
    outside `tests/test_cli.py`, the `PENDING` removal, and the
    `tabs`/`trailing_whitespace` optional classification.

    Routing to step 3 for finding 2 alone. On its return the gates
    re-run in order — step 4, then step 5.

### 2026-09-05T21:00:00+00:00

Author: software-engineer/software-engineering/git,python,testing

    Revision complete, scoped to finding 2 alone. All sections of the
    issue are present and complete per `templates/ISSUE.md`; nothing
    blocked the step and no edit was disputed.

    One change, in `tests/linter/rules/test_unicode.py`: the orphaned
    `Config gating` banner and its trailing blank lines are deleted.
    Five lines removed, no other file touched, no test added, removed,
    renamed or altered.

    Verified orphaned before deleting rather than taking the finding on
    its word. The banner was immediately followed by the
    `Configuration validation (key level)` banner with nothing between
    them, and `git diff main..HEAD` on the file shows why: the two
    tests that lived under `Config gating` —
    `test_missing_allowed_returns_empty` and
    `test_allowed_none_returns_empty` — were rewritten as
    `test_missing_allowed_raises` and `test_allowed_wrong_type_raises`
    under the new banner at commit 4cb8cb4, leaving the old one heading
    nothing. The section it named no longer exists; the tests it used
    to name do, under a banner that describes them accurately.

    The sibling banners were checked and left alone.
    `test_elements.py:12` and `test_links.py:24` still carry
    `Config gating` with tests under them and are correct as they
    stand. Minor correction to the review for the record:
    `test_tabs.py` and `test_trailing_whitespace.py` have no
    `Config gating` banner at all, so there was nothing to preserve
    there either way. Nothing turns on it — no file but
    `test_unicode.py` was modified.

    Definition of Done. `flake8 tiredize tests` is clean. Full suite:
    844 passed / 50 skipped / 0 failed — unchanged from the step-3 and
    step-4 numbers, as a comment-only deletion should leave them. All
    50 skips are the pre-existing `gfm-parity` skips in the markdown
    parser tests, confirmed by reading every skip reason.
    `tests/test_main_module.py` has zero skip markers, re-verified by
    grep: the only `skip` occurrences in that file are a runtime
    `pytest.skip` inside the `_console_script` helper for when the
    console script is absent from PATH, and the word "Unskipped" in
    three docstrings. No `@pytest.mark.skip` and no `PENDING`.
    Coverage is unaffected — no source file changed.

    Finding 1 (`README.md:237`) was not touched, per the routing.
    `README.md` is byte-for-byte unchanged on this branch since before
    the revision.

    Nothing new for triage. The observations recorded at steps 3 and 4
    stand as written and were not acted on.

### 2026-09-05T22:00:00+00:00

Author: program-manager

    Step 3's revision is back. Routing to step 4, code and test review,
    iteration 2 of the 5 allowed. On a clean verdict the gates continue
    in order to step 5, acceptance verification; the pipeline stops
    there and returns to the user regardless of outcome, because the
    user approved re-running the gates, not the steps beyond them.

    Scope of this iteration. The step-4 review at
    2026-09-05T20:00:00+00:00 recorded a clean verdict on the source and
    the tests and listed, item by item, what it had checked and found
    correct. Nothing in `tiredize/` changed since. The reviewer should
    confirm the one change that did land — the five deleted comment
    lines in `tests/linter/rules/test_unicode.py` at 5653386 — and
    should not re-review the items the previous iteration already
    cleared. Re-reviewing settled ground is how a capped loop gets
    spent on nothing.

    Two things the reviewer is asked to confirm specifically, both
    raised by step 3's revision comment rather than by the diff:

      - That deleting the banner left the surviving
        `Configuration validation (key level)` section correctly
        headed, with no test orphaned or misfiled by the removal.
      - Step 3 recorded a correction to the previous review's finding
        2: `test_tabs.py` and `test_trailing_whitespace.py` carry no
        `Config gating` banner at all, so the review's claim that their
        banners "still have tests under them" was wrong on those two
        files. Nothing turns on it — neither file was touched — but the
        reviewer should confirm the correction rather than let the
        record stand with an error in it.

    Finding 1 from iteration 1 — `README.md:237` documenting behaviour
    criterion 9 removed — is deferred to step 8 and is deliberately not
    fixed on this branch. It is not an outstanding step-4 finding and
    should not be re-raised here. If step 7 decides no user
    documentation is warranted, the architect is asked to say where
    finding 1 goes; that carry-forward is recorded at
    2026-09-05T20:00:00+00:00 and still stands.

    State at routing. `flake8 tiredize tests` clean; suite 844 passed /
    50 skipped / 0 failed, the 50 all pre-existing gfm-parity skips.
    Verified directly at routing time, not carried over from step 3's
    report.

### 2026-09-05T23:00:00+00:00

Author: software-engineer/software-engineering/code-review,python,testing

    Code and test review, iteration 2 of 5. Verdict: clean. No
    findings in any category. No action tag raised.

    All sections of the issue are present and complete per
    `templates/ISSUE.md` — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments — and nothing blocked the
    step.

    Scope honoured. Per the routing at 2026-09-05T22:00:00+00:00 the
    items the 2026-09-05T20:00:00+00:00 iteration listed as checked
    and found correct were treated as settled and not re-derived.
    Finding 1 (`README.md:237`) is deferred to step 8 and is not
    re-raised here; `README.md` is byte-for-byte unchanged since that
    review, confirmed by `git diff 84f32be HEAD -- README.md` being
    empty.

    The change under review, confirmed. `git diff --stat 84f32be HEAD
    -- . ':!.context/issues'` shows exactly one file changed:
    `tests/linter/rules/test_unicode.py`, 5 deletions, 0 insertions.
    `git diff --stat 84f32be HEAD -- tiredize/` is empty, so the
    source is untouched since the clean verdict. The deleted lines are
    the `Config gating` banner and its two trailing blank lines —
    comment text only, no code, no test.

    Confirmation 1 — the surviving section is correctly headed. In the
    file as it now stands, `Configuration validation (key level)` sits
    at lines 13-19, directly after the imports, and heads four tests:
    `test_missing_allowed_raises`, `test_allowed_wrong_type_raises`,
    `test_unknown_key_raises` and
    `test_unknown_key_reported_before_bad_element_name`. All four are
    key-level configuration checks, which is what the banner names, so
    none is orphaned or misfiled by the removal. The banner's body
    text explaining why `allowed` is required survived the deletion
    intact. No test was added, removed, renamed or reordered — the
    diff is deletions only, and the suite count is unchanged. The
    later `Config validation` banner at line 240 still heads the two
    value-level checks (`test_unknown_exclude_element_raises`,
    `test_non_string_exclude_entry_raises`); it is pre-existing, not
    in the diff, and describes its tests accurately.

    Confirmation 2 — step 3's correction is right, and iteration 1 was
    wrong. `grep -rn "Config gating" tests/` returns exactly two hits
    across the whole test tree: `test_links.py:24` and
    `test_elements.py:12`. `tests/linter/rules/test_tabs.py` and
    `tests/linter/rules/test_trailing_whitespace.py` carry no
    `Config gating` banner at all, so the previous iteration's
    sentence "the equivalent banners in `test_elements.py`,
    `test_links.py`, `test_tabs.py` and `test_trailing_whitespace.py`
    still have tests under them" was incorrect on the last two named
    files — there is no such banner in either to have tests under.
    The error was in the review's prose only; it produced no wrong
    edit, since step 3 touched neither file. The correction is
    confirmed and stands.

    The two banners that do exist were re-checked and are not
    orphaned: `test_elements.py:12` heads
    `test_empty_disallow_returns_empty` and
    `test_unknown_element_name_raises`; `test_links.py:24` heads
    `test_validate_false_returns_empty`. Both sections have content,
    and neither file was modified.

    Findings by category:

      - Unused parameters or dead code -- none found. The banner that
        was the previous iteration's only entry in this category is
        gone, and its removal introduced no new dead comment or
        unreferenced helper.
      - Duplicate or redundant logic -- none found.
      - Missing input validation -- none found.
      - Inconsistencies between parallel code paths -- none found.
      - Silent acceptance of invalid input -- none found.
      - Reachable bugs or error-handling gaps -- none found.
      - Contract violations -- none found.
      - Spec fidelity gaps -- none found on this branch's code and
        tests. (`README.md:237` is deferred to step 8 by PM routing
        and is deliberately not counted here.)
      - File organization violations -- none found.
        `tiredize/linter/rules/unicode.py` still has exactly one test
        file, `tests/linter/rules/test_unicode.py`, and the deletion
        moved nothing between files.

    Definition of Done, observed directly rather than carried over.
    `flake8 tiredize tests` is clean. Full suite: 844 passed / 50
    skipped / 0 failed — identical to the step-3 and iteration-1
    numbers, as a comment-only deletion should leave them. All 50
    skips are the pre-existing gfm-parity skips in the markdown parser
    tests, confirmed by counting skip reasons with `pytest -rs`: 50 of
    50 lines carry `gfm-parity:`. `tests/test_main_module.py` still
    has zero skip markers — the only `skip` occurrences are the
    runtime `pytest.skip` in the `_console_script` helper at line 74
    and the word "Unskipped" in three docstrings. Working tree clean.
    Coverage was not re-measured: no source file changed since the
    iteration-1 measurement, so the figures recorded there still hold.

    Nothing new for triage. The observations recorded at steps 3 and 4
    stand as written and were not acted on.

### 2026-09-06T00:00:00+00:00

Author: program-manager

    Step 4 is clean at iteration 2 of 5. No findings in any category, no
    action tag raised, and both items the routing asked for came back
    confirmed: the surviving `Configuration validation (key level)`
    banner heads four key-level tests with nothing orphaned, and step 3's
    correction to iteration 1's finding 2 is right — `Config gating`
    exists only in `test_links.py` and `test_elements.py`, so iteration
    1's claim about `test_tabs.py` and `test_trailing_whitespace.py` was
    wrong in its prose. That error is now corrected on the record and
    produced no wrong edit.

    Finding 1 (`README.md:237`) remains deferred to step 8 and was
    correctly not re-raised. The carry-forward recorded at
    2026-09-05T20:00:00+00:00 still stands: if step 7 decides no user
    documentation is warranted, the architect is asked to say where
    finding 1 goes rather than leaving it unrouted.

    Routing to step 5, acceptance verification. The qa-engineer
    independently re-runs the Definition of Done and confirms the
    contract black-box through the public interface — it does not take
    step 3's or step 4's numbers on their word, and it does not review
    internals, which is step 4's concern and now settled.

    Two notes for that step, both already in the record. Criterion 8
    (`.context/specifications/cli.md`) and the second half of criterion
    10 (`.context/specifications/linter.md` documenting the rule-module
    convention) are the technical-architect's at step 6 and are not yet
    satisfiable; the step-2 comments at 2026-09-05T14:00:00+00:00 and
    2026-09-05T16:00:00+00:00 record that both are verified by
    inspection rather than by test, and the linter.md half is explicitly
    named as a step-5 inspection item. Verify what exists; do not treat
    the unwritten specifications as a failure of this branch.

    The pipeline stops after step 5 and returns to the user regardless
    of outcome. The user approved re-running the two gates, not the
    steps beyond them.

### 2026-09-06T01:00:00+00:00

Author: qa-engineer/software-engineering/testing

    Acceptance verification, iteration 1 of 5. Verdict: pass. The
    contract holds end to end through the public interface. No
    findings, and no action tag raised.

    All sections of the issue are present and complete per
    `templates/ISSUE.md` — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments — and nothing blocked the
    step.

    Definition of Done, observed here rather than carried over.
    `flake8 tiredize tests` clean, exit 0. Full suite: 844 passed /
    50 skipped / 0 failed, matching the step-3 and step-4 numbers.
    All 50 skips are the pre-existing `gfm-parity` skips in the
    markdown parser tests — confirmed by reading every reason under
    `pytest -rs`, all 50 prefixed `gfm-parity:` and none in
    `tests/test_main_module.py`. Coverage 99% overall (1553
    statements, 11 uncovered); `tiredize/__main__.py` 100%,
    `tiredize/linter/utils.py` 100%, `cli.py` 98%, and every
    uncovered line is one of the pre-existing gaps step 3
    enumerated. Working tree clean before and after; every fixture I
    wrote went to a scratchpad outside the repository.

    The acceptance tier, identified from the outside. The four
    black-box classes in `tests/test_main_module.py` —
    `TestExitStatus`, `TestStreamParity`,
    `TestIssueAssigneeVocabulary`, `TestRuleConfigurationValidation`
    — are 43 of the file's 49 items and all 43 pass with zero skips.
    `TestModuleExecution` (6 items) sits below an explicit banner
    marking it the step-3 white-box tier and was excluded from the
    acceptance run. The file carries no `@pytest.mark.skip` and no
    `PENDING`; the only `skip` is the runtime guard in
    `_console_script` for an absent console script, and it did not
    fire — so the console-script cases genuinely ran.

    Entry-point identity checked first, because parity is worthless
    if the two entry points are different builds. `tiredize` on PATH
    resolves to `/home/admin/.local/bin/tiredize`, an editable
    install whose project location is this working tree, and it
    imports `tiredize.cli:main` from the same tree `-m` executes.
    The two entry points are the same code.

    Independent black-box exercise, not the suite. I drove 59
    argument lists through both entry points — 118 process
    invocations — comparing exit status, stdout and stderr on every
    one. Parity held on all 59, and every exit status observed
    across the whole sweep fell in {0, 1, 2}. Even the argparse
    usage text matches, because `prog` is pinned to `tiredize`
    rather than defaulting to `__main__.py`.

    By criterion:

    1. `-m` exits with exactly what `main()` returns. Confirmed by
       hand at all three values. `0`: one clean document, two clean
       documents, and all three configuration flags together. `1`,
       findings: all three categories the contract names — a
       markdown schema mismatch, a `line_length` violation, and a
       frontmatter `value_not_allowed`. `1`, runtime errors: five
       kinds — a missing input document, a missing configuration
       file, an unparseable configuration file, an unknown rule id,
       and an invalid schema (an unrecognized section key), each on
       stderr. `2`: all three usage permutations — no arguments,
       paths with no configuration flag, configuration flag with no
       paths — plus both argparse paths, an unknown flag and a flag
       missing its value.

    2. `__main__.py` propagates `main()`'s return value. Its whole
       observable consequence is criterion 1, confirmed above. The
       module is `raise SystemExit(main())`, the idiom Design
       Decisions prefers.

    3. A subprocess test asserts `0`, `1` and `2`.
       `test_clean_document_exits_zero`,
       `test_markdown_schema_finding_exits_one` and
       `test_no_arguments_exits_two` all spawn
       `sys.executable -m tiredize` and all pass.

    4. `tests/test_cli.py` passes unchanged bar the one carve-out.
       `git diff main..HEAD -- tests/test_cli.py` is exactly two
       hunks: `max_length` to `maximum_length` inside
       `test_valid_document_passes_rules`, which criterion 4 permits
       by name, and one wholly new test. No other existing test in
       the file is edited or deleted. The file runs 22 passed.

    5. Identical stdout, stderr and exit status. Held on all 59
       argument lists, including the case most likely to diverge: a
       document mixing emoji, accented Latin and CJK. Offsets are
       character-based and correct — `😴` is one character at column
       2, `🛌` at column 21 — so no astral-plane or byte-offset
       discrepancy separates the entry points.

    6. A runtime error aborts the run, on both entry points. Missing
       document first and a clean document after: the later path is
       absent from stdout entirely. Clean, missing, clean: only the
       first path is reported, the second errors to stderr, the
       third is never reached. Findings-continue confirmed as the
       counterpart — a document with findings followed by a clean
       one reports both and exits `1`. Findings followed by a
       runtime error prints the findings, then aborts on the error.

    7. Assignee vocabulary. `git diff main..HEAD` on
       `.context/schemas/issue-frontmatter.yaml` is the assignee list
       alone: `PM` removed, `program-manager` added, order matching
       upstream. `context-process-migration.md` now carries
       `assignee: program-manager`, and no `assignee: PM` survives
       anywhere in the repository. All ten files in
       `.context/issues/` validate clean against both project
       schemas, exit `0`, through both entry points.

    8. `.context/specifications/cli.md` — see below.

    9. An invalid rule configuration is a runtime error. All three
       states verified by hand on the CLI, each exiting `1` with the
       rule id and the offending key on stderr, and each aborting.
       The negative case holds too: an omitted optional key stays
       legal and exits `0` — checked for `line_length.exclude`,
       `unicode.exclude`, the four optional `links` keys, and
       `tabs.allowed` / `trailing_whitespace.allowed` under their
       optional classification. "Required means present, not
       truthy" holds: `links: {validate: false}` and
       `elements: {disallow: []}` both exit `0`.

    10. Every built-in rule validates its configuration this way.
        Confirmed across all six non-private rule modules
        individually, not by sampling: for each of `elements`,
        `line_length`, `links`, `tabs`, `trailing_whitespace` and
        `unicode` I ran a valid baseline (exit `0`), the same
        baseline plus a key no rule accepts (exit `1`, rule id and
        key on stderr), and an accepted key holding a wrong-typed
        value (exit `1`, rule id and key on stderr). The
        required-key-omitted state was verified on all four keys
        classified required — `line_length.maximum_length`,
        `unicode.allowed`, `elements.disallow`, `links.validate`.
        A useful cross-check fell out of this: the "Accepted keys:"
        list each rule reports matches the README's documented
        option table for that rule exactly, all six.

    The two step-6 items, verified by inspection and reported as
    state rather than as findings, per the routing.

      - Criterion 8. `.context/specifications/cli.md` does not
        exist. Not authored; the technical-architect's at step 6.
      - Criterion 10, second half. `.context/specifications/
        linter.md` exists but does not yet document the convention.
        Its "Rule Module Convention" section lists three
        requirements — non-private filename, a `validate` signature,
        `rule_id=None` — and none of them mentions validating
        configuration. Its "Configuration Helpers" section lists the
        five `get_config_*` accessors and still says they return
        `None` when a key is missing or wrong-typed with "No
        exceptions raised on type mismatch"; `validate_config` is
        absent from it. Reading the section as the step-2 comment
        asked — would a new rule author following it alone write the
        check? — the answer today is no. That is the gap step 6
        closes, and it is not a defect in this branch's code.

    Neither is treated as a failure here and neither is routed as an
    edit request. `README.md:237` is deferred to step 8 by PM
    routing and was not re-raised.

    Boundary sweep, beyond the named criteria, looking for any way
    the contract could be violated outside the tested paths. An
    empty rules file, an empty document, a duplicate path, and
    findings from two subsystems on one document all behave per the
    contract. A directory given as a path is a runtime error, exits
    `1`, and aborts. `--help` exits `0` on both entry points. No
    invocation anywhere in the sweep produced an exit status outside
    {0, 1, 2}, wrote a finding to stderr, or wrote a runtime error
    to stdout.

    Observations for triage, outside the ten criteria and not acted
    on:

      - Criterion 7 says "every file in `.context/issues/`". Read
        recursively that would include `.context/issues/completed/`,
        whose 20 archived files do not validate: they are v1-format
        issues with `Out of Scope` and `Completion Report` sections,
        no `Comments` section, and no `workflow`/`tags`/`knowledge`
        fields. I checked before reporting it: not one of those
        failures is assignee-related, the required fields that
        trigger them were already required on `main`, and the
        schema's own documented Usage line and the gate-2-approved
        `test_every_issue_file_validates_clean` both use the
        non-recursive `*.md` glob. So the archive is outside the
        criterion's scope on the approved reading, and its state is
        untouched by and unrelated to this branch. Recorded only so
        the reading is explicit on the record rather than implicit,
        and because whoever finishes `context-process-migration`
        will meet it.
      - A rule block with a null body (`line_length:` and nothing
        under it) still reports `Invalid configuration for rule
        line_length: None` from the engine, naming the rule but not
        the missing key. Exit `1` on stderr, so the contract holds;
        this is the pre-existing behaviour step 4 already recorded,
        confirmed unchanged from the outside.

### 2026-09-06T02:00:00+00:00

Author: program-manager

    Both review gates are now clean. Step 4 passed at iteration 2 of 5
    with no findings; step 5 passed at iteration 1 of 5 with no
    findings. Neither raised an action tag, and neither routed anything
    back to step 3. The implementation on this branch has passed white-
    box code and test review and independent black-box acceptance
    verification.

    Pipeline stopped here by instruction. The user approved re-running
    the two gates, not the steps beyond them, so step 6 (technical
    reference) was not started. The issue stays `status: in-review`,
    `step: acceptance-verification`, `assignee: qa-engineer` until the
    user routes it onward.

    Three items carried forward for whoever resumes, none of them
    outstanding findings against this branch:

      - Criterion 8. `.context/specifications/cli.md` does not exist
        yet. It is the technical-architect's at step 6.
      - Criterion 10, second half. `.context/specifications/linter.md`
        exists but does not document the configuration-validation
        convention: its "Rule Module Convention" section names three
        requirements, none about configuration, and its "Configuration
        Helpers" section still describes the accessors as returning
        `None` on a missing or wrong-typed key with no exception
        raised, which the implementation has superseded.
        `validate_config` is absent from it. Step 6's.
      - Finding 1 from step 4 iteration 1 — `README.md:237` telling
        readers that omitting `unicode.allowed` disables the rule —
        remains deferred to step 8 and deliberately unfixed. The
        carry-forward at 2026-09-05T20:00:00+00:00 stands: if step 7
        decides no user documentation is warranted, the architect is
        asked to say where it goes rather than leaving it unrouted.

    Two observations the step-5 verifier recorded for triage are left
    as recorded and were not acted on: the recursive-versus-glob
    reading of criterion 7's "every file in `.context/issues/`" with
    respect to the archived `completed/` files, and the null rule-
    configuration block being reported by the engine without naming the
    missing key.

### 2026-09-06T03:00:00+00:00

Author: program-manager

    Both gates are clean — step 4 iteration 2 found nothing, step 5
    passed on the first pass. Routing to step 6, technical reference.

    Two acceptance criteria are outstanding and both are this step's:

      - Criterion 8. `.context/specifications/cli.md` does not exist.
        The scoping seed at `### Seed the CLI specification here`
        governs what it should contain.
      - Criterion 10, second half. `.context/specifications/linter.md`
        exists but does not document the configuration-validation
        convention. Step 5 read it against the test step 2 set — would
        a new rule author following the spec alone write the check? —
        and found the answer is no. Its "Configuration Helpers" section
        still says the accessors return `None` on missing or wrong type
        and that no exception is raised on type mismatch, which the
        implementation has made false; `validate_config` is absent.

    So step 6 is not a no-op on this issue: contracts changed, and the
    architect is expected to produce a specification rather than record
    that none is needed. The judgment of scope within that remains the
    architect's.

    One item to carry, not to act on. Finding 1 from step 4 iteration 1
    — `README.md:237` telling readers that omitting `unicode.allowed`
    disables the rule, which criterion 9 turned into a runtime error —
    is deferred to step 8 and is deliberately unfixed on this branch.
    The architect decides at step 7 whether the documentation track
    runs. If that decision is "no documentation required", finding 1
    has no home, and the architect is asked to say where it goes rather
    than leaving it unrouted.

    Routing step 6 alone. The pipeline returns to the user before step
    7, because step 7 carries the documentation-track decision and that
    is worth surfacing rather than passing through.

### 2026-09-06T04:00:00+00:00

Author: technical-architect/software-engineering/specifications

    Technical reference. Verdict: contracts changed; two
    specifications written. No open question raised, so the step
    completed rather than stopping.

    All sections of the issue are present and complete per
    `templates/ISSUE.md` — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments — and nothing blocked the
    step.

    Assessment of the diff, made against `git diff main..HEAD`
    rather than against the issue's description of it. Three
    contract changes, in two subsystems:

      - The process exit status of `python -m tiredize`. A public
        entry point's observable status changes for every path that
        returns rather than raises.
      - `main()`'s abort semantics. A missing input document now
        returns `1` immediately (`cli.py:133-141`) instead of
        setting the status and continuing, so the rule is uniform:
        errors abort, findings continue. This lands on both entry
        points, not just `-m`.
      - The rule-module convention. `validate_config()` is new
        public surface in `tiredize/linter/utils.py`, every one of
        the six built-in rules calls it as the first statement of
        `validate()`, and four rules that previously returned `[]`
        for an absent required key now raise `ValueError`. What was
        a silent no-op is now a runtime error that aborts the run.

    The scoping seed directed a `cli.md`, and the assessment agrees
    with it independently: the first two items alone would have
    required one whether or not the criteria named it, and the third
    would have required the `linter.md` update on its own.

    What was written.

    `.context/specifications/cli.md` — new, following
    `templates/SPECIFICATION.md`. Overview states the CLI's ownership
    and its boundary against the parser, the linter and the two
    validators, and says in its own paragraph that the document is
    partial: it covers the exit-status contract and the stream and
    abort semantics only, and silence on flags, output format and
    configuration resolution is an unwritten section rather than an
    absence of behavior, with a pointer to `tiredize/cli.py` for
    anything not covered. Contracts and Interfaces gives the two
    entry points, the parity requirement between them, and `main()`'s
    signature with the returns-rather-than-exits contract and the
    argparse exception to it. File Layout covers four files. The
    domain section, Exit Status Contract, holds the status table, the
    findings-versus-runtime-errors split with the exception types the
    subsystems raise, the errors-abort/findings-continue semantics
    including the consequence that a run ending in a runtime error is
    not a complete report, the per-path processing order, and the
    stream table. Four Design Decisions.

    Scope held to the seed. Nothing in `cli.md` documents the flags
    beyond naming the three whose absence is a usage error, and
    nothing documents output format beyond the finding line's shape,
    which the parity and stream contracts depend on. `### Out of
    scope` is respected.

    `.context/specifications/linter.md` — updated in four places.
    Rule Module Convention gains a fourth requirement — declare the
    accepted and required keys, call `validate_config()` first — with
    a worked module skeleton, so the step-2 test ("would a new rule
    author following the spec alone write the check?") is answerable
    from that section without reading a rule's source. Configuration
    Helpers now carries `validate_config()`'s signature and corrects
    the two sentences the implementation falsified: the accessors
    still return `None` for both missing and wrong-typed keys and
    still raise nothing, but that is now stated as the reason they
    cannot police configuration themselves, and the section says what
    `None` means inside a rule once `validate_config()` has run. A
    new domain section, Rule Configuration Validation, covers the
    three fault states, the fixed reporting order and why unknown
    keys come first, the five-name type vocabulary and the bool/int
    guard, the required-versus-optional principle with the per-rule
    key table for all six rules, and the key-level-only boundary
    against the value-level checks rules perform themselves. Design
    Decisions replaces "None recorded yet." with five entries.

    Design Decisions migrated from this issue, per the step's
    instruction to carry across anything whose reversal would
    materially change the subsystem:

      - `### Errors abort the run` → `cli.md`, with the batch-
        validator alternative recorded as the alternative rather than
        as history.
      - `### Validating rule configuration` → `linter.md`, split into
        four: the shared helper over per-rule checks, key sets
        declared in the module rather than on `Rule`, configuration
        mistakes as errors rather than degraded rules, and "enabling
        a rule must never be a no-op" as what settles required versus
        optional.
      - `### Fix idiom` is recorded as contract, not as decision:
        `cli.md` states that `__main__.py` must raise the status and
        that a caller discarding the return value discards the
        failure signal. `raise SystemExit` versus `sys.exit` is
        repository consistency and does not change behavior, so it is
        not a Design Decision.

    Not migrated, deliberately: the test-file naming and organization
    decision, the `__main__.py` coverage approach, the step-ownership
    decisions, and the assignee-vocabulary fix. The first three are
    process and test-suite history; the fourth is project tooling and
    belongs to no subsystem specification.

    Two decisions recorded in `cli.md` that came from the code rather
    than from the issue's Design Decisions: `main()` returning rather
    than exiting, and `prog="tiredize"` being pinned in the parser.
    The second is load-bearing for criterion 5 — without the pin,
    argparse derives `prog` from `sys.argv[0]` and renders it as
    `__main__.py` under module execution, and the stream-parity
    contract fails on every usage message. Step 5 observed the parity;
    the specification now records why it holds.

    Criterion status, in my own assessment.

      - Criterion 8. Met. `.context/specifications/cli.md` exists,
        follows the template's section order, documents the exit-code
        contract, and documents both the findings-continue and the
        errors-abort semantics, which the criterion names explicitly.
      - Criterion 10, second half. Met.
        `.context/specifications/linter.md` documents the convention
        as a numbered requirement of the rule-module convention, with
        the declaration skeleton, the classification principle and the
        per-rule key table. Applying step 5's test to the updated
        text: a new rule author reading Rule Module Convention and
        Rule Configuration Validation has the requirement, the shape
        of the declaration, the rule for classifying each key, and the
        consequence of skipping it. The answer is now yes.

    I do not tick the checkboxes; they are the PM's.

    One scope note, so it is on the record rather than silent.
    `linter.md`'s File Layout listed four rule modules and omitted
    `elements.py`, `unicode.py` and `_elements.py` — stale before this
    branch, unrelated to it. I corrected it because the section I
    added enumerates the accepted keys of all six rules, and leaving
    the layout naming four would have put a contradiction inside the
    document I was writing. `utils.py`'s entry gained
    `validate_config`, which is this branch's change. Nothing else in
    the file's pre-existing content was touched.

    One observation for triage, not acted on. `.context/PROJECT.md`
    lists the CLI under Architecture but carries no
    `Spec: specifications/cli.md` pointer, where all four other
    subsystems do. A reader following PROJECT.md will not find the new
    document. It is one line, in a file outside this issue's criteria,
    so I have left it for the PM to route.

    `README.md:237` is deferred to step 8 and was not touched, per the
    routing. The step-7 documentation-track decision is not made here.

    Action: @workflow-owner — process improvement

    `knowledge/specifications.md` has no guidance for authoring a
    deliberately partial specification, which is what criterion 8
    required. Its structure section assumes a specification describes
    its subsystem whole, and "a specification is a reference, not a
    history" gives no way to say "this section does not exist yet"
    without it reading as a TODO — which the same file forbids. I
    resolved it by stating the partiality in the Overview as a
    scope boundary rather than as planned work, and by pointing the
    reader at the source for what is not covered. That reading is
    mine, not the knowledge file's. Since seeding a specification from
    one issue and growing it across later ones is a pattern this
    project will hit again, the knowledge file is worth a short
    paragraph saying how a partial specification declares its own
    boundary. Raising it for closeout, not blocking on it.

### 2026-09-06T05:00:00+00:00

Author: program-manager

    User ratified the architect's out-of-scope correction to
    `.context/specifications/linter.md`'s File Layout section. The list
    named four of the six rule modules, omitting `elements.py`,
    `unicode.py` and `_elements.py`; it was stale before this branch and
    is not covered by any of this issue's ten acceptance criteria.

    Kept as part of this issue. The architect's reasoning holds: the
    section it added immediately below enumerates the accepted
    configuration keys of all six rules, so leaving the layout at four
    would have shipped a document contradicting itself two sections
    apart. The correction is confined to that list.

    Recorded here so the scope exception is on the record rather than
    absorbed silently, per the scope-discipline rule. The architect
    declared it rather than burying it, which is the behaviour the rule
    is meant to produce.

### 2026-09-06T06:00:00+00:00

Author: technical-architect/software-engineering/specifications

    Addendum to step 6. `.context/PROJECT.md` now carries the CLI's
    specification pointer: `Spec: `specifications/cli.md`.` added to
    the CLI paragraph under Architecture, matching the form the four
    subsystem entries already use — own line, backticked path relative
    to `.context/`, trailing period, last in the entry. Placing it last
    put the list lead-in `It orchestrates three subsystems:` into its
    own paragraph; every existing word and the colon are preserved
    verbatim and nothing else in the file changed.

    This was the triage observation recorded at
    2026-09-06T04:00:00+00:00, which the user has ratified as a scope
    exception in the same way as the `linter.md` File Layout
    correction. It is a directed change, not initiative, and it is on
    the record as an exception rather than as a criterion.

    No other staleness in `PROJECT.md` was acted on, and none was
    found while making the edit. No action tag raised. Step 7 is not
    entered here and `README.md:237` is untouched.

### 2026-09-06T07:00:00+00:00

Author: program-manager

    Step 6 delivered `.context/specifications/cli.md` and the
    configuration-validation additions to `linter.md`, plus two
    user-ratified scope exceptions recorded at 05:00 and 06:00. Routing
    to step 7, architecture review.

    Two things this step owes, beyond the standard verdict:

      - Criteria 8 and 10's second half are the architect's own
        assessment from step 6 and have not been independently checked.
        Step 7 is where that check happens. The checkboxes stay
        unticked until it does; the PM ticks them, and only on step 7's
        confirmation, so no role signs off on its own work.
      - The user-documentation decision, seeded yes at scoping. The
        decision is the architect's, biased toward running.

    The documentation decision carries a dependency the seed does not
    name. Step 4 iteration 1 found `README.md:237` — the `unicode`
    rule's option table saying that omitting `allowed` disables the
    rule, which criterion 9 turned into a runtime error. That finding
    was deferred to step 8 and is deliberately unfixed on this branch.
    If the documentation track runs, step 8 must cover both the Usage
    section named in the scoping seed and the rule reference at README
    lines 182-300, which the seed does not name. If the decision is
    "no documentation required", finding 1 has no home and the
    architect is asked to say explicitly where it goes rather than
    leaving it unrouted.

    The scoping seed's note about `python -m` versus `python3 -m` on
    machines that ship only `python3` carries forward to whoever writes
    the prose. Recorded here so it is not lost between steps.

### 2026-09-06T08:00:00+00:00

Author: technical-architect/software-engineering/specifications

    Architecture review. Verdict: one finding, and it is in the
    reference rather than in the code. The change's system-design
    impact is sound and nothing routes back to step 3.
    `.context/specifications/linter.md` is accurate as written.
    `.context/specifications/cli.md` is accurate except for one
    statement about argparse which, read together with the sentence
    it refers back to, tells a reader that `--help` exits `2` when it
    exits `0`. That routes to step 6 alone. The user-documentation
    decision is made below and does not depend on the finding.

    All sections of the issue are present and complete per
    `templates/ISSUE.md` — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments — and nothing blocked the
    step.

    System-design impact, assessed against `git diff main..HEAD`
    rather than against the issue's account of it.

      - Contracts. Three changed, in two subsystems: the process exit
        status of `python -m tiredize` (`__main__.py:19`); `main()`'s
        abort semantics, where a missing input document now returns
        `1` immediately (`cli.py:133-141`) and so changes the console
        script too; and the rule-module convention, where
        `validate_config()` is new public surface in
        `tiredize/linter/utils.py:105` and four rules that returned
        `[]` for an absent required key now raise. No contract was
        broken unintentionally — each of the three is a criterion.
      - Coupling. The new dependency runs rules → `utils`, the same
        direction as the pre-existing `get_config_*` dependency, so
        no new edge crosses a subsystem boundary. Nothing about a
        rule's key set reaches the `Rule` dataclass or
        `discover_rules()`; `tiredize/linter/rules/__init__.py` is
        untouched on this branch. The new `ValueError` leaves
        `run_linter()` through the exception channel the CLI already
        caught at `cli.py:152-157`, which is why the CLI needed no
        change to absorb a new error class. That is the reason the
        blast radius stopped where it did, and it is worth stating:
        the change reused an existing boundary instead of widening
        one.
      - Patterns. Uniform across all six rules. Each declares
        `_RULE_ID`, `_ALLOWED_KEYS` and `_REQUIRED_KEYS` at module
        level and calls `validate_config()` as the first statement
        after its docstring — `elements.py:40`, `line_length.py:80`,
        `links.py:70`, `tabs.py:38`, `trailing_whitespace.py:38`,
        `unicode.py:82`. I checked all six rather than sampling.
      - The one boundary enforced by prose alone. `discover_rules()`
        requires only a `validate` function, so a custom rule from a
        third-party package that skips `validate_config()`
        reinstates the silent no-op, and no test can catch it —
        `tests/linter/rules/test_loader.py` guards the built-ins
        only. This follows directly from the deliberate decision to
        declare key sets in the module rather than on `Rule`, and
        `linter.md` states the requirement as non-optional, which is
        the strongest instrument the chosen design leaves. Recorded
        as a consequence, not as a finding.

    Criterion 8, checked independently against the code rather than
    taken on step 6's word. I read `cli.md` line by line against
    `tiredize/cli.py`, `tiredize/__main__.py`,
    `tiredize/markdown/types/document.py`, `pyproject.toml`, the
    installed console script, and both entry points run by hand.

      - Template conformance. Overview, Contracts and Interfaces,
        File Layout, one domain section (Exit Status Contract),
        Design Decisions — the template's sections in the template's
        order, none invented, none missing, and the Overview carries
        the ownership and boundary statement the template asks for.
      - `main()`'s signature at `cli.md:57` matches `cli.py:95`
        exactly, return type included. `raise SystemExit(main())` at
        `cli.md:50` matches `__main__.py:19`. The console-script
        claim checks out from both ends: `pyproject.toml:28-29`
        declares `tiredize = "tiredize.cli:main"` and the generated
        script on PATH ends in `sys.exit(main())`.
      - The status table matches the code at every exit. `2` at
        `cli.py:116-125` for both usage permutations; `1` from
        findings at `cli.py:205-206`; `1` from runtime errors at
        `cli.py:141`, `162`, `181` and `199`; `0` as the `exit_code`
        initialized at `cli.py:127` and returned at `cli.py:209`.
      - The runtime-error exception list — `FileNotFoundError`,
        `ValueError`, `yaml.YAMLError`, `RuleNotFoundError`,
        `AmbiguityError` — is exactly the set caught across
        `cli.py:133-199`, no more and no fewer.
      - Findings-continue and errors-abort, which the criterion names
        explicitly, are both documented and both true of the code:
        every error handler returns, findings set `exit_code` and
        fall through the loop.
      - Per-path order (load, then rules, markdown schema,
        frontmatter schema) matches `cli.py:129-199`, and
        accumulate-then-print matches `cli.py:143` with `201-208`.
      - The stream table matches: usage to stderr at
        `cli.py:119-124`, `error: {exc}` to stderr at `137`, `158`,
        `177` and `196`, findings and the per-file line to stdout at
        `204` and `208`. The `line_col()` claim — 1-based line,
        0-based column, one column per character — matches
        `document.py:35-50`.
      - `prog="tiredize"` at `cli.py:26` is real and is load-bearing
        as the specification says: with it, both entry points emit
        the same usage text, which is what makes criterion 5 hold on
        the usage-error path.

      So criterion 8's substance holds: the document exists, follows
      the template, and documents the exit-code contract with both
      processing semantics. The single defect is the finding below,
      and it sits inside the exit-code contract itself, which is what
      the criterion names — so I would not have the checkbox ticked
      until it is corrected. I do not tick it either way; that is the
      PM's.

    Criterion 10, second half, checked the same way against
    `tiredize/linter/utils.py`, the six rule modules and
    `tiredize/linter/engine.py`.

      - Rule Module Convention gains requirement 4 at
        `linter.md:63-66`, with the "not optional and not a
        convenience" paragraph and a worked skeleton at
        `linter.md:76-92` whose shape matches `line_length.py:19-24`
        and `line_length.py:62-90`.
      - `validate_config()`'s signature at `linter.md:105-110`
        matches `utils.py:105-110` exactly. The two sentences the
        implementation falsified are corrected in place: the
        accessors do still return `None` for both a missing and a
        wrong-typed key and still raise nothing (`utils.py:40-102`),
        and the section now gives that as the reason they cannot
        police configuration, plus what a `None` means inside a rule
        once `validate_config()` has run.
      - Fault states and their fixed order — unknown keys, then
        omitted required keys, then wrong-typed values, raising
        rather than accumulating — match `utils.py:152-180`
        statement for statement.
      - The type vocabulary table matches `_CONFIG_TYPE_CHECKS` at
        `utils.py:19-28`, including the bool-excluded-from-int guard
        at `utils.py:22-25` and the reason given for it.
      - The required-versus-optional table was checked key by key
        against all six modules' `_ALLOWED_KEYS` and
        `_REQUIRED_KEYS`. It matches all six with no key missing and
        none invented: `elements` requires `disallow`; `line_length`
        requires `maximum_length` and takes `exclude`; `links`
        requires `validate` and takes `exclude`, `headers`,
        `timeout`, `valid_status_codes`; `tabs` and
        `trailing_whitespace` require nothing and take `allowed`;
        `unicode` requires `allowed` and takes `exclude`.
      - The key-level-only boundary is true of the code: the
        value-level `ValueError`s in `line_length`, `unicode`,
        `elements` and `links` are unchanged and still run after the
        helper.
      - Applying step 5's test myself, and deliberately in that
        order: I read Rule Module Convention and Rule Configuration
        Validation first, without a rule module open, and then
        checked what I would have written against a real rule. The
        sections give the requirement, the shape and position of the
        declaration, the principle for classifying each key, the
        table for the existing ones, and the consequence of skipping
        the call. A new rule author following the specification alone
        writes the check. The answer is yes.

      Criterion 10's second half is met, on my own reading rather
      than on step 6's. Confirmed for the PM to tick.

    Judgment of `cli.md`'s declared partial scope. Honestly drawn,
    with one qualification.

      - The declaration at `cli.md:20-26` names what it covers
        (exit-status contract, stream and abort semantics) and names
        what it does not (the flags, the finding output format beyond
        the shape the parity contract needs, configuration
        resolution), says in terms that the silence is an unwritten
        section rather than an absence of behavior, and points the
        reader at `tiredize/cli.py` for the rest. The silences are
        declared, not accidental.
      - It covers what it claims to cover. All three statuses are
        specified, every kind of output the code writes appears in
        the stream table, and the abort semantics are given with
        their consequence — that a run ending in a runtime error is
        not a complete report — which is the part a reader would
        otherwise have to derive.
      - It stays inside the boundary. The three flags appear only
        where their absence is a usage error; the finding line's
        shape appears only because the parity and stream contracts
        depend on it. Nothing documents a flag's semantics, the
        configuration search, or the renderer. `### Out of scope`'s
        ban on expanding beyond the exit-code contract is respected,
        and I looked for a breach rather than assuming one was
        absent.
      - The qualification: the one place the document is wrong is
        inside the half it claims, not in the half it declined. A
        partial specification is judged on whether its covered part
        is right, and that is exactly where the finding lands.

    Finding — `cli.md` misstates the exit status of `--help`. Routes
    to step 6 alone, then step 7 again. It does not touch the
    implementation and nothing goes back to step 3.

      `cli.md:64-67` enumerates argparse's own errors as "an unknown
      flag, a flag missing its value, `--help`". `cli.md:90-92` then
      says "Argparse's own errors also exit `2`, by raising
      `SystemExit(2)` from within `main()`". Taken together the
      document states that `--help` exits `2`. It exits `0` —
      verified by running it, against `python3 -m tiredize` (`2`) and
      `python3 -m tiredize --bogus x` (`2`) as controls. `--help`
      also writes to stdout, which the stream table at
      `cli.md:132-137` does not cover, and the `0` row of the status
      table ("Every path was loaded and produced no findings") does
      not describe a `--help` invocation either, though the section
      opens by claiming every invocation exits one of exactly three
      statuses.

      Why this is worth a round rather than a shrug: the document's
      whole subject is which status a given invocation produces, its
      intended reader is someone wiring a CI or pre-commit gate, and
      the statement it gets wrong is a status code. That is the same
      class of defect the issue was opened to fix.

      It is not inherited from the issue. The Public Contract in
      Summary lists argparse's errors as "unknown flag, missing flag
      value" and does not include `--help`. The enumeration is step
      6's own addition, which is what makes this the reference's
      error rather than the implementation's.

      The correction is one sentence and its shape is step 6's call;
      the straightforward version separates `--help` from the error
      paths and states that it prints to stdout and exits `0`.
      Nothing else in either specification needs an edit.

      Non-blocking nit, for step 6 to take or leave while it is in
      the file: `cli.md:76` describes `tests/test_main_module.py` as
      "Process-level tests of `-m`", but three of its five classes
      drive the console script, and one of those,
      `TestRuleConfigurationValidation`, exercises linter
      configuration rather than the CLI. "Process-level tests of both
      entry points" would be truer. This is not a finding and the
      review does not turn on it.

    Action: @program-manager — request for edit

    User-documentation decision: yes. Steps 8 and 9 run. Logged here
    with the reasoning, per the step's instruction, and it stands
    independently of the finding above.

      The seed said yes and the workflow biases toward running;
      neither is a reason on its own, so here is the independent
      case. Three user-visible changes land on this branch and none
      of them is documented anywhere a user reads.

        1. `python -m tiredize` now gates. The README's Usage section
           (`README.md:63-100`) is pitched at precisely this use —
           "suitable for pre-commit hooks and CI/CD pipelines" — yet
           never mentions module invocation and describes exit
           behavior as "returns a nonzero exit code when validation
           fails", which does not separate `1` from `2`.
        2. Errors now abort. `tiredize --rules r.yaml docs/*.md` with
           one missing file used to report the survivors and now
           stops at the first. That is a behavior change for existing
           console-script users, not only for `-m`, and nothing
           user-facing says so.
        3. A rules file that used to run can now hard-fail. Criterion
           9 turns an unknown key, a wrong-typed value and an omitted
           required key into runtime errors that abort. Anyone whose
           rules file carries `max_length` — the exact typo this
           repository's own test suite shipped — meets it on upgrade.

      Item 3 decides it on its own: this is a breaking configuration
      change for existing users, and the document those users consult
      is wrong about it in at least one place. Declining the
      documentation track would ship a behavior change that only the
      specifications record, and specifications are for contributors,
      not users.

      What step 8 must cover, since the scoping seed names only part
      of it:

        - The Usage section (`README.md:63-100`): the three exit
          statuses and what each means, the module invocation, and
          the errors-abort/findings-continue rule.
        - The rule reference (`README.md:182-300`), which the seed
          does not name. Finding 1 from step 4 iteration 1 lives here
          — `README.md:237` tells the reader that omitting
          `unicode.allowed` disables the rule, which criterion 9 made
          a runtime error, so a reader following it writes a
          configuration that hard-fails. Alongside it, the section
          marks no key as required and does not say that an
          unrecognized or wrong-typed key is now an error. The two
          overlap: line 237 is where the section is wrong, the
          missing required/optional marking is where it is
          incomplete. Step 4 iteration 1 raised the first, step 3 the
          second; they should be treated together.

      So `README.md:237` lands at step 8, inside the documentation
      track. The contingency recorded at 2026-09-05T20:00:00+00:00 —
      that a "no documentation" decision would leave it unrouted —
      does not fire.

      Carried forward for whoever writes the prose, from the scoping
      seed: this issue says `python -m tiredize` throughout, but many
      machines ship only `python3` and the machine this was scoped on
      is one of them. Reader-facing documentation should not tell
      people to run a command that may not exist — write `python3 -m
      tiredize`, or give both forms. Tests are unaffected; they
      invoke `sys.executable`.

    Observations for triage, outside the ten criteria and not acted
    on.

      - `README.md:316-350`, the Custom Rules section, teaches a rule
        skeleton with no `validate_config()` call and tells the
        reader the module need only "expose a `validate` function".
        After this branch that is a user-facing instruction to write
        a rule that swallows configuration typos in silence — the
        failure mode criteria 9 and 10 exist to remove. It is a third
        README site this change falsifies, beyond the Usage section
        and the rule reference, and it falls outside the ten criteria
        and outside both scope exceptions the user has ratified. I am
        naming it rather than folding it into step 8's scope: if it
        is to be fixed on this branch it needs the user's
        ratification as a third exception, and otherwise it is a
        separate issue. Either way it should not be lost.
      - `linter.md`'s URL Validation section shows `check_url_valid`
        without its `valid_status_codes` parameter, which
        `utils.py:192-200` has. Stale on `main` before this branch,
        untouched by step 6, and unrelated to this issue's changes.
      - `.context/PROJECT.md` says the CLI "orchestrates three
        subsystems" and then lists four. Also pre-existing on `main`;
        the specification-pointer addition at `08b1cab` did not
        introduce it and correctly did not act on it.
      - `tests/linter/rules/test_loader.py:139` asserts that every
        built-in rule declares at least one key ("a rule with no keys
        cannot be configured"), while `linter.md:94-96` says a rule
        accepting no keys still calls `validate_config()` with an
        empty `_ALLOWED_KEYS`. Both are defensible — the
        specification describes the convention including custom
        rules, the guard pins the built-ins — but a future built-in
        with no configuration keys would fail a guard the
        specification does not mention. Noted so the tension is on
        the record.

    On the process-improvement item raised at
    2026-09-06T04:00:00+00:00: I met the same gap from the other
    side. `knowledge/specifications.md` gives no criterion for
    *judging* a partial specification either, so the standard I
    applied at step 7 — does it cover what it claims, and are its
    silences declared rather than accidental — is mine rather than
    the knowledge file's. That supports the existing item; I am not
    raising a second tag for it.

### 2026-09-06T09:00:00+00:00

Author: program-manager

    Step 7 raised one edit request. Routing it to step 6 alone, per the
    workflow's rule that an inaccurate technical reference goes back to
    step 6 and then to step 7 again. Nothing routes to step 3, so steps
    4 and 5 do not re-run — the finding is in the specification, not in
    the code, and step 7 confirmed the implementation sound.

    The finding: `.context/specifications/cli.md:64-67` lists `--help`
    among argparse's own errors, and `cli.md:90-92` says those exit 2.
    `--help` exits 0 and writes to stdout. It is step 6's own addition,
    not inherited from the issue — the Summary's Public Contract names
    only unknown flag and missing flag value. Correcting it also means
    the stream table and the exit-0 row should account for `--help`
    writing to stdout.

    Also in scope for this revision, the nit step 7 recorded alongside:
    `cli.md:76` describes `tests/test_main_module.py` as process-level
    tests of `-m`, when three of its five classes drive the console
    script.

    Criterion 8 stays unticked until this lands. Step 7 confirmed the
    substance of `cli.md` against the code path by path, but the place
    it is wrong sits inside the half the document claims to cover, so
    the criterion is not yet met. Criterion 10's second half was
    independently confirmed and is met; the PM ticks both together once
    step 7 re-runs clean, so no role signs off on its own work.

    Documentation decision, logged by the architect at
    2026-09-06T08:00:00+00:00: the track runs. Steps 8 and 9 are in.
    `README.md:237` therefore lands at step 8 and the no-home
    contingency does not fire.

### 2026-09-06T10:00:00+00:00

Author: technical-architect/software-engineering/specifications

    Step 6 revision. Scoped to step 7's finding and the nit recorded
    alongside it; `.context/specifications/cli.md` is the only file
    changed. `linter.md` was not opened — step 7 confirmed it accurate
    key by key and it is out of this revision's scope. No code, no
    `README.md`, no `.context/PROJECT.md`.

    `--help` verified first-hand rather than taken on the finding's
    word, on this machine, which ships `python3` and not `python`.
    `python3 -m tiredize --help` exits `0`, writes 718 bytes to stdout
    beginning `usage: tiredize [-h] ...`, and writes nothing at all to
    stderr. The console script agrees: `tiredize --help` exits `0` with
    an empty stderr. Controls, all `2` and all on stderr:
    `python3 -m tiredize` (no arguments), `python3 -m tiredize --bogus
    x`, and `python3 -m tiredize --rules` (flag missing its value). So
    the finding is correct in both halves — the status and the stream —
    and the document was wrong about both.

    Four edits, all inside the exit-status contract the document
    already claims:

      - `main`, the argparse paragraph. It previously listed `--help`
        alongside the two error forms under one sentence, which the
        later "argparse's own errors also exit `2`" sentence then
        turned into a claim that `--help` exits `2`. The paragraph now
        splits the two: argparse's own errors — unknown flag, flag
        missing its value — print to stderr and raise `SystemExit(2)`;
        `--help` is not an error, prints to stdout and raises
        `SystemExit(0)`. Both are still named as the one place
        `main()` exits instead of returning, which is the fact that
        paragraph exists to carry.
      - Exit Status Contract, the `0` row: "Every path was loaded and
        produced no findings, or `--help`". The section opens by
        claiming every invocation exits one of exactly three statuses,
        so a `--help` invocation had to be described by one of the
        three rows; it is now described by the row it actually takes.
      - The prose under the status table, which is where the `2` claim
        was made. Argparse's own errors are now enumerated where they
        are claimed rather than by reference to an earlier sentence,
        and `--help` is excluded explicitly, with its status and its
        stream.
      - Output Streams gains two rows: `--help` text to stdout, and
        argparse's own error messages to stderr. The second is not
        part of the finding but is the same omission seen from the
        other side — the table claimed to enumerate every stream the
        CLI writes to and did not cover either argparse path.

    The nit, taken rather than left: `cli.md:76` described
    `tests/test_main_module.py` as "Process-level tests of `-m`". The
    file has five classes. `TestExitStatus` drives `-m` by subprocess;
    `TestStreamParity` drives both entry points; and
    `TestIssueAssigneeVocabulary` and `TestRuleConfigurationValidation`
    drive the console script — so three of five touch the console
    script, and the last of those exercises linter configuration rather
    than the CLI. `TestModuleExecution` is in-process, through
    `runpy.run_module`, so "process-level" was not true of the file
    either. The cell now reads "Entry-point tests, subprocess and
    in-process", which is true of all five without misdescribing any.
    I did not take step 7's suggested wording verbatim because
    "process-level" is the half that is wrong for `TestModuleExecution`.

    Nothing else changed. No section was added or removed, the partial-
    scope declaration is untouched, and the document still stops at the
    exit-status contract and its stream and abort semantics, per
    `### Out of scope`. The correction is entirely inside the half the
    document claims to cover, which is where step 7 said the defect
    sat. Criterion 8 is back with step 7 to confirm; I do not tick it.

    No action tag raised. Nothing about the revision needed a decision
    that was not already recorded.

### 2026-09-06T11:00:00+00:00

Author: program-manager

    Step 6's scoped revision landed at `50c5209`. Routing back to step 7,
    architecture review, iteration 2 of 5.

    The revision is confined to `.context/specifications/cli.md` and is
    the only thing that changed since step 7 iteration 1. `linter.md`,
    the code, `README.md` and `.context/PROJECT.md` are untouched.

    Scope of this iteration. Iteration 1 confirmed the implementation
    sound with nothing routing to step 3, confirmed `linter.md` accurate
    key by key, and confirmed criterion 10's second half met. That ground
    is settled and is not re-derived. What step 7 re-checks now is the
    corrected `cli.md` and, on the strength of it, criterion 8 — which
    iteration 1 withheld not because `cli.md`'s substance was unverified,
    but because the one error sat inside the half the document claims to
    cover.

    The user-documentation decision was made and logged by the architect
    at 2026-09-06T08:00:00+00:00: the track runs, steps 8 and 9 are in,
    and `README.md:237` lands at step 8. That decision stands and is not
    revisited at this iteration.

    Still not in scope, and still with the user as a separate decision:
    `README.md:316-350`, the Custom Rules section teaching a rule
    skeleton with no `validate_config()` call, raised as a triage
    observation at 2026-09-06T08:00:00+00:00. It is outside the ten
    criteria and outside both ratified scope exceptions.

    Criterion 8 and criterion 10's second half stay unticked until step 7
    returns clean; the PM ticks both together, so no role signs off on
    its own work.

### 2026-09-06T12:00:00+00:00

Author: technical-architect/software-engineering/specifications

    Architecture review, iteration 2. Verdict: clean. No findings, no
    action tag, nothing routes anywhere. The `--help` correction is
    right and complete, step 6 introduced no new inaccuracy and stayed
    inside the scoped revision, and **criterion 8 is now met** —
    confirmed for the PM to tick alongside criterion 10's second half,
    which iteration 1 already confirmed.

    All sections of the issue are present and complete per
    `templates/ISSUE.md`, and nothing blocked the step.

    `--help` verified first-hand rather than on step 6's or iteration
    1's word, on this machine, which ships `python3` and not `python`.
    Measured, not inferred:

      - `python3 -m tiredize --help` — exit `0`, 718 bytes on stdout
        beginning `usage: tiredize [-h] [--rules RULES_PATH]`, zero
        bytes on stderr.
      - `tiredize --help` (console script at
        `/home/admin/.local/bin/tiredize`) — exit `0`, the same 718
        bytes on stdout, zero on stderr. Byte-identical to the module
        form, so the parity contract at `cli.md:39-41` holds on this
        path too, which is the `prog="tiredize"` pin at `cli.py:26`
        doing its job.
      - `python3 -m tiredize -h` — identical to `--help`. The short
        form takes the same path.
      - Controls, all exit `2` with an empty stdout and everything on
        stderr: no arguments (306 bytes), `--bogus x` (239),
        `--rules` with its value missing (247), and `tiredize --bogus
        x` (239) through the console script.
      - The status is genuinely `SystemExit(0)` and not `SystemExit(None)`
        dressed up by the shell: driving the module body in-process
        through `runpy.run_module("tiredize", run_name="__main__")`
        with `sys.argv` patched to `--help` yields
        `SystemExit.code == 0`, 718 characters captured from stdout
        and nothing from stderr. That matters because `cli.md:69-70`
        now claims `SystemExit(0)` specifically, and it unwinds
        through `raise SystemExit(main())` at `__main__.py:19`
        untouched, exactly as that module's own comment says.

    So both halves of iteration 1's finding are confirmed independently
    — the status and the stream — and the corrected document is right
    about both.

    Completeness of the correction. I went back through every site in
    `cli.md` that bears on `--help`, not only the two the finding
    named, and each is now consistent:

      - `cli.md:65-70`, the `main` argparse paragraph. Splits the two
        kinds of argument that raise from inside `main()`: argparse's
        own errors (unknown flag, flag missing its value) to stderr
        with `SystemExit(2)`, and `--help` to stdout with
        `SystemExit(0)`. Both are still named as the one place `main()`
        exits instead of returning, which is the fact the paragraph
        exists to carry and which `cli.py:113-114` and the docstring at
        `cli.py:95-112` bear out.
      - `cli.md:83`, "exactly three statuses". Now honest, because the
        `0` row at `cli.md:87` covers `--help` explicitly. This was the
        subtler half of the finding — the claim was falsified not by
        what any row said but by a case no row described — and it is
        closed.
      - `cli.md:94-97`, the prose under the status table. This is where
        the `2` claim was made by back-reference; argparse's errors are
        now enumerated at the point they are claimed, and `--help` is
        excluded by name with its status and its stream. The
        back-reference that produced the wrong reading is gone, not
        merely qualified.
      - `cli.md:137-144`, Output Streams. Two rows added: the `--help`
        text to stdout, and argparse's own error messages to stderr.
        Both verified above. The second is beyond the finding and is
        the right kind of over-delivery — the table claims to
        enumerate every stream the CLI writes to, and it covered
        neither argparse path before, so fixing only the `--help` half
        would have left the table still incomplete on its own terms.
      - `cli.md:146`, "Findings never go to stderr and runtime errors
        never go to stdout" — unaffected; `--help` is neither.
      - The Design Decisions at `cli.md:167-176` — the `prog` pin and
        "three statuses, no more" — both still hold, and the `prog`
        pin is now load-bearing on one more path than before.

    I checked the one place a reader might still trip and judged it
    sound rather than letting it pass unexamined: the stderr row at
    `cli.md:143` reads "The usage message and the usage-error
    explanation", while the `--help` text also opens with a `usage:`
    line and goes to stdout. The row pairs the usage message with the
    usage-error explanation, which scopes it to the usage-error path,
    and the stdout row two lines above names the `--help` text
    outright. No finding; recorded only so it is on the record that it
    was looked at.

    No new inaccuracy, and no stray outside the scoped revision.
    `git diff 45e31e9 50c5209` touches two files: the issue's Comments
    section and `.context/specifications/cli.md`. The `cli.md` diff is
    five hunks and every one is inside the exit-status contract the
    document already claims — no section added or removed, the
    partial-scope declaration at `cli.md:20-26` untouched, `### Out of
    scope`'s ban on expanding beyond the exit-code contract respected.
    I looked for a breach rather than assuming its absence.

    The File Layout nit, taken by step 6, is accurate. The cell now
    reads "Entry-point tests, subprocess and in-process". Checked
    against the file: `tests/test_main_module.py` has five classes —
    `TestExitStatus` (subprocess, `-m`), `TestStreamParity` (both entry
    points), `TestIssueAssigneeVocabulary` and
    `TestRuleConfigurationValidation` (console script), and
    `TestModuleExecution` (in-process, `runpy.run_module`). The new
    wording is true of all five. Step 6 was right not to take my
    suggested phrasing verbatim: "process-level" is false of
    `TestModuleExecution`, so its replacement is better than the one I
    proposed.

    Criterion 8: **met.** The document exists, follows
    `templates/SPECIFICATION.md`, and documents the exit-code contract
    including the findings-continue and errors-abort semantics — all
    verified path by path against the code at iteration 1 and not
    re-derived here. The sole reason iteration 1 withheld it was that
    the one defect sat inside the half the document claims to cover.
    That defect is corrected, the correction is consistent everywhere
    it bears, and nothing new was introduced. The qualification is
    discharged and the criterion is met. I do not tick it; that is the
    PM's, so no role signs off on its own work.

    Criterion 10's second half stands as confirmed at
    2026-09-06T08:00:00+00:00. `linter.md` was not reopened and did not
    need to be.

    The settled ground, confirmed unmoved rather than re-derived.
    `git diff --stat 76ed4f0 HEAD` — from iteration 1's own verdict
    commit to the tip — lists exactly two files: this issue and
    `.context/specifications/cli.md`. No file under `tiredize/` or
    `tests/` changed, `linter.md` did not change, and neither did
    `README.md` or `.context/PROJECT.md`. So iteration 1's findings on
    system-design impact — contracts, coupling and patterns all sound,
    nothing routing back to step 3 — and its key-by-key confirmation of
    `linter.md` stand unchanged on their own terms.

    User-documentation decision: unchanged and not revisited. The
    decision was made and logged by the architect at
    2026-09-06T08:00:00+00:00 — the track runs, steps 8 and 9 are in,
    and `README.md:237` lands at step 8, so the no-home contingency
    does not fire. It stands.

    `README.md:316-350`, the Custom Rules section, remains a triage
    observation with the user as a separate decision. Out of scope
    here, not acted on, not folded into anything.

    No action tag. Step 7 is clean and the review loop closes at
    iteration 2 of 5.

### 2026-09-06T13:00:00+00:00

Author: program-manager

    Step 7 iteration 2 came back clean and the review loop closed. All
    ten acceptance criteria are now ticked. Recording what each tick
    rests on, because the PM ticks them and no role signs off on its own
    work:

      - Criteria 1-7, 9 and the code half of 10 rest on step 5's
        independent acceptance verification, which drove 59 argument
        lists through both entry points — 118 process invocations — and
        checked criteria 9 and 10a against all six built-in rules
        individually rather than by sample.
      - Criterion 8 and the specification half of 10 rest on step 7,
        which checked both specifications against the implementation
        path by path rather than accepting step 6's account. Criterion
        8 was withheld at iteration 1 over the `--help` error and
        confirmed at iteration 2 after step 6 corrected it.

    User-ratified scope exception, the third on this issue. Step 7
    iteration 1 flagged that `README.md:316-350`, the Custom Rules
    section, teaches a rule skeleton with no `validate_config()` call
    and says a module need only expose a `validate` function. After
    this branch that instructs a reader to write exactly the silent
    config-typo swallowing criterion 9 exists to prevent. The user has
    ratified folding it into step 8 rather than opening a separate
    issue: step 8 is already rewriting two other README sections for
    this same change, so it is one more section in the same pass by the
    same writer, reviewed at step 9. The alternative ships a README
    that contradicts itself.

    Step 8's scope is therefore three README sites, not one:

      - The Usage section at `README.md:63-100`, per the scoping seed —
        the `-m` invocation and the `0`/`1`/`2` contract, where it
        currently says only "nonzero exit code".
      - The `unicode` rule's option table at `README.md:237`, step 4
        finding 1 — `allowed` is required, not "omitting this option
        disables the rule".
      - The Custom Rules section at `README.md:316-350`, this
        exception.

    Two constraints for the prose author, both already on the record and
    repeated so they are not lost at the hand-off. Errors-abort is a
    behaviour change for existing console-script users, not only for
    `-m`. And this issue says `python -m tiredize` throughout, but many
    machines ship only `python3` — including the one this issue was
    scoped on, where `python` returns 127. Reader-facing prose must not
    tell people to run a command that may not exist.

    Routing to step 8, user documentation, ghostwriter.

### 2026-09-06T14:00:00+00:00

Author: ghostwriter/software-engineering

    Step 8, user documentation. Wrote the three README sites the PM
    scoped at 2026-09-06T13:00:00+00:00. `README.md` is the only file
    changed — no code, no tests, no specification, and nothing in this
    issue outside the Comments section. No acceptance criterion was
    ticked or unticked.

    All sections of the issue are present and complete per
    `templates/ISSUE.md`, and nothing blocked the step. No knowledge
    files were loaded: `AGENTS.md` maps none to the
    `user-documentation` step and the issue's frontmatter `knowledge`
    field is empty, so I worked from my base function and took the
    voice, wrapping (prose to 72 columns) and table conventions from
    `README.md` itself rather than inventing a mapping. The
    orchestrator is reporting that gap to the PM separately.

    Site 1 — the Usage section. Two edits, and the exit-status
    material is now its own `### Exit status` subsection rather than
    the single sentence that used to close the section.

      - The section intro now names both invocation forms, states
        that they take the same arguments and produce the same output
        on the same streams with the same status, and says module
        execution is the safer choice in a pre-commit hook or CI job
        where the console script may not be on `PATH`. The worked
        examples still use the console script, and the text says so.
      - The old closing sentence — "prints rule violations in
        `file:line:col: [rule_id] message` format and returns a
        nonzero exit code when validation fails" — is replaced by an
        output paragraph naming both streams and the `no issues
        found.` line, then a three-row status table (`0`, `1`, `2`)
        with the `--help` and argparse cases folded into the rows
        they actually take, then the findings-versus-runtime-errors
        distinction, then errors-abort. The "suitable for pre-commit
        hooks and CI/CD pipelines" pitch is kept, attached now to the
        three statuses rather than to "nonzero".
      - Errors-abort is written as a property of the tool, not of
        `-m`: "Errors abort and findings continue, whichever way you
        invoke the tool", with a console-script example
        (`tiredize --rules rules.yaml intro.md missing.md guide.md`)
        showing the run stopping at the missing file. The consequence
        a reader would otherwise have to derive is stated: a run that
        exited `1` is a complete report only when the `1` came from
        findings.

    Site 2 — the rule reference. The wrong line and the incomplete
    section are treated together, as the architect and the PM
    directed.

      - `unicode.allowed` no longer says "Omitting this option
        disables the rule." It is marked required, with the reason —
        the key selects the mode the rule runs in.
      - Every one of the six option tables gains a **Required**
        column. The classification follows `linter.md`'s table and I
        checked it against `_REQUIRED_KEYS` in all six rule modules
        rather than taking it on the specification's word: `elements`
        requires `disallow`; `line_length` requires `maximum_length`;
        `links` requires `validate`; `unicode` requires `allowed`;
        `tabs` and `trailing_whitespace` require nothing. Where a key
        is optional and its default was not already stated, the
        default is now stated — `exclude` defaults to no exemptions,
        and `tabs`/`trailing_whitespace` still forbid their target
        with `allowed` absent.
      - The Linter Rules intro gains the key-validation rules: the
        three faults, that each names the rule and the offending key
        on stderr and aborts with status `1`, and that an omitted
        optional key remains legal. The unknown-key message is quoted
        verbatim from a real run. It also carries the
        present-not-truthy point with `links: {validate: false}` as
        the example, so a reader does not read "required" as "must be
        enabled".

    Site 3 — Custom Rules, the third ratified scope exception. The
    skeleton now declares `_RULE_ID`, `_ALLOWED_KEYS` and
    `_REQUIRED_KEYS` at module level, imports `validate_config` from
    `tiredize.linter.utils`, and calls it as the first statement of
    `validate()`. Following prose says the call is not optional and
    why, how to classify a key as required or optional, the five type
    names, and that a rule accepting no keys still calls it with an
    empty `_ALLOWED_KEYS`. Step 2 no longer leaves "expose a
    `validate` function" as the whole requirement: it now says
    discovery checks nothing beyond that, so nothing stops a rule
    that omits the call from loading — the boundary step 7 recorded
    as enforced by prose alone is stated to the reader as such rather
    than hidden.

    The `python3` constraint. Reader-facing prose never instructs
    `python -m tiredize`. The two-form code block gives `tiredize`
    and `python3 -m tiredize`, and `python -m tiredize` appears once,
    as a conditional: write it "only where `python` is known to be
    the Python 3 interpreter tiredize was installed into — many
    systems ship `python3` and no `python` at all". That keeps the
    form available to readers whose `python` is correct (a venv, a
    Windows install) without telling anyone to run a command that may
    not exist. Confirmed on this machine: `python` is not found.

    Verified by running, not taken from the issue or the
    specifications. Every status and every error message that appears
    in the new prose was produced first:

      - Clean input `0`, findings `1`, no arguments `2` — through
        `python3 -m tiredize` and through the console script, same
        output and same status.
      - `--help` exits `0` with zero bytes on stderr, on both entry
        points. `--bogus x` and `--rules` with its value missing both
        exit `2`.
      - The three configuration faults, each exiting `1`:
        `unknown configuration key 'max_length'. Accepted keys:
        exclude, maximum_length.` (the line now quoted in the
        README), `required configuration key 'allowed' is missing.`,
        and `configuration key 'maximum_length' expects an integer,
        got 'str': '80'.`
      - Errors abort: `intro.md missing.md guide.md` with `missing.md`
        absent reports the error, reports `intro.md`, never processes
        `guide.md`, and exits `1` — on both entry points. A missing
        rules file and an unknown rule id also exit `1`.
      - The optional-key claims: `tabs: {}` still flags a tab, and
        `links: {validate: false}` is accepted and exits `0`.
      - The Custom Rules skeleton itself, executed in-process. The
        import path resolves, the call passes a good config, and it
        raises the three documented `ValueError`s — including the
        empty-`_ALLOWED_KEYS` case, which produces "This rule accepts
        no configuration keys."

    Taken from the specifications rather than re-derived: nothing of
    substance. `cli.md`'s stream table and `linter.md`'s type
    vocabulary and required/optional table informed the wording, and
    both were checked against the code — the key sets against the six
    rule modules, the statuses and streams against runs.

    Observation for triage, not acted on and not a fourth site this
    change falsified. `README.md`'s Features section says built-in
    rules "cover line length, tab usage, trailing whitespace, and
    link validation", omitting `unicode` and `elements`, which both
    have full reference subsections further down. That is
    pre-existing on `main` — this branch neither introduced nor
    worsened it — so it is outside step 8's scope and I left it
    alone. Recording it so it is not lost. Beyond it I found no
    README site this change falsified or made misleading: the only
    other exit-status claim in the file was the "nonzero exit code"
    sentence, which site 1 replaced, and no other section mentions
    module invocation or rule-key handling.

    No action tag raised.

### 2026-09-06T15:00:00+00:00

Author: program-manager

    Step 8 landed at `a643275`. Routing to step 9, documentation review,
    iteration 1 of 5. Frontmatter set to `status: in-review`,
    `step: documentation-review`, `assignee: proofreader`.

    What step 8 delivered, and therefore what step 9 reviews. Three
    README sites, exactly the three the routing at
    2026-09-06T13:00:00+00:00 named, and nothing else. The Usage section
    gained both invocation forms and an `### Exit status` subsection with
    a three-row table, replacing the "returns a nonzero exit code"
    sentence. The rule reference gained a `Required` column on all six
    option tables, the corrected `unicode.allowed` row, and a
    key-validation paragraph in the Linter Rules intro. The Custom Rules
    skeleton gained `_RULE_ID`, `_ALLOWED_KEYS`, `_REQUIRED_KEYS` and the
    `validate_config()` call. `README.md` and this issue's Comments
    section are the only files in the diff; no criterion was ticked or
    unticked and nothing under `tiredize/`, `tests/` or
    `.context/specifications/` was touched.

    No action tag was raised at step 8. Nothing blocked it.

    Two constraints step 8 was given and step 9 should check were
    honoured. Errors-abort had to be written as a behaviour change for
    existing console-script users, not only for the module invocation —
    step 8 reports writing it as a property of the tool and illustrating
    it with a console-script example. And reader-facing prose must not
    instruct `python -m tiredize`, because many machines ship only
    `python3`, including the one this issue was scoped on. Step 8 reports
    using `tiredize` and `python3 -m tiredize` in the examples and
    admitting `python -m tiredize` only once, as a conditional for
    readers whose `python` is the right interpreter. Both are the
    reviewer's to verify rather than take on the writer's word.

    Scope for this step. Step 9 reviews the whole README, not only the
    changed sections — a change can contradict preexisting wording, and
    the step file requires the full document. But the review's remit is
    findings, not fixes, and any correction it requests routes back to
    step 8 within the same three sites. If step 9 finds a *fourth* README
    site this change falsified, it records it as a triage observation and
    stops rather than requesting a fix: the user has ratified three scope
    exceptions on this issue already and expects to be asked about a
    fourth. Step 8 already recorded one such observation — the Features
    section omitting `unicode` and `elements` from its list of built-in
    rules — and correctly judged it pre-existing on `main` rather than
    falsified by this branch.

    The review loop is capped at 5 iterations. All ten acceptance
    criteria are ticked and stay ticked; step 9 neither ticks nor unticks
    any of them.

### 2026-09-06T16:00:00+00:00

Author: proofreader/software-engineering

    Documentation review, iteration 1. Verdict: two findings, both
    inside the three sites step 8 owns, both routing back to step 8.
    Everything else in the README is accurate against the
    implementation, and I found no fourth site this change falsified.

    All sections of the issue are present and complete per
    `templates/ISSUE.md` — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments — and nothing blocked the
    step. No acceptance criterion was ticked or unticked; all ten
    stay as the PM left them.

    The standard I applied, stated rather than left implicit. No
    knowledge files were loaded: `AGENTS.md` maps none to the
    `documentation-review` step and the issue's frontmatter
    `knowledge` field is empty, so I worked from my base function.
    Accuracy I judged against the code and against the running
    program. Prose quality I judged against the README's own
    established voice, wrapping (prose to 72 columns) and table
    conventions rather than against a style knowledge file — the
    standard there is mine, not a knowledge file's. The orchestrator
    is reporting the mapping gap to the PM separately.

    Finding 1 — `README.md:114-116` describes an output order the
    tool does not produce.

      The sentence reads: "The command prints rule violations to
      stdout in `file:line:col: [rule_id] message` format, followed
      by a `file: no issues found.` line for every file that came
      back clean."

      "Followed by" asserts that the clean-file lines come after the
      violations. They do not. `cli.py:129-208` processes one path at
      a time and prints that path's output before moving to the next,
      so the two kinds of line interleave in argument order. Measured
      on this machine, with `intro.md` and `guide.md` clean and
      `bad.md` over the limit:

          $ tiredize --rules rules.yaml intro.md bad.md guide.md
          intro.md: no issues found.
          bad.md:3:80: [line_length] Line exceeds maximum length of 80 (120 found).
          guide.md: no issues found.

      The clean line precedes the violation, which is the opposite of
      what the sentence promises. There is a second half to it: a
      file that produced violations never also gets a `no issues
      found.` line (`cli.py:205-208` is an either/or), so the
      sentence can also be read as promising a per-file summary line
      that never arrives.

      This matters because the paragraph is the reader's only account
      of what the tool writes to stdout, and it sits immediately
      above the `### Exit status` section whose purpose is precision
      about the same run.

      Correction: state that output is grouped per file, in the order
      the paths were given, and that each file yields either its
      violations or the clean line. For example — "For each file, in
      the order given, the command prints that file's rule violations
      to stdout as `file:line:col: [rule_id] message`, or a single
      `file: no issues found.` line if it has none. Runtime errors go
      to stderr as `error: <message>`." The final sentence is already
      correct and can stand as it is.

    Finding 2 — `README.md:401-440`, the Custom Rules skeleton
    introduces `_RULE_ID` and never says what it is or how it relates
    to the rule ID the engine actually uses.

      The skeleton declares three module-level constants under one
      comment — "Every key this rule accepts, mapped to its type, and
      the subset it requires" — which describes `_ALLOWED_KEYS` and
      `_REQUIRED_KEYS` and does not describe `_RULE_ID` at all. The
      prose that follows (lines 425-440) explains the
      `validate_config()` call, how to classify a key as required or
      optional, the five type names, and the empty-`_ALLOWED_KEYS`
      case. `_RULE_ID` is explained nowhere.

      A reader is therefore left to guess, and the README tells them
      two things that pull apart. `README.md:450` says "The rule ID
      is derived from the module filename (e.g., `my_rule.py`
      produces rule ID `my_rule`)", which is true —
      `rules/__init__.py:63-72` computes it from the module name and
      `engine.py:70` stamps it onto every result. But `_RULE_ID` is a
      hand-written string that the engine never reads: it appears
      only in `validate_config()`'s error messages
      (`utils.py:160-180`). Set it to anything other than the
      filename and the tool reports configuration errors against a
      rule id that does not exist in the reader's rules file, while
      findings from the same rule are labelled with the filename.
      Nothing in the README, and nothing in `linter.md`, warns of it.

      Correction: one sentence in the prose at `README.md:425-440`
      saying what `_RULE_ID` is for and that it must match the module
      filename — for example, "`_RULE_ID` names the rule in
      `validate_config()`'s error messages; keep it equal to the
      module filename, which is the ID the engine uses and the one
      readers write in their rules file." While the sentence is being
      added, the comment above the constants is worth widening from
      the key sets to all three names, since as written it describes
      two of the three.

    The two constraints, both verified rather than taken on step 8's
    word.

      - Errors-abort is written as a property of the tool, not of
        `-m`. `README.md:146` reads "Errors abort and findings
        continue, whichever way you invoke the tool", and the worked
        example at `README.md:151` is a console-script run. The
        `### Exit status` section names no invocation form in its
        table or in either of the findings/runtime-error paragraphs.
        Nothing frames the change as `-m`-only. Honoured. I also
        confirmed the behaviour is genuinely shared: `tiredize
        --rules rules.yaml intro.md missing.md guide.md` and the same
        arguments through `python3 -m tiredize` both print
        `intro.md: no issues found.` to stdout, `error: Path does not
        exist: missing.md` to stderr, never touch `guide.md`, and
        exit `1`.
      - Reader-facing prose never instructs `python -m tiredize`.
        `grep -n "python -m" README.md` returns exactly one line,
        `README.md:78`, and it is the conditional step 8 described:
        "Write `python -m tiredize` only where `python` is known to
        be the Python 3 interpreter tiredize was installed into —
        many systems ship `python3` and no `python` at all." The
        invocation block at `README.md:69-72` gives `tiredize` and
        `python3 -m tiredize`. The resolution holds throughout the
        file; there is no second occurrence anywhere. Honoured. On
        this machine `python` is not found and `python -m tiredize`
        returns 127, so the caveat is not hypothetical.

    Verified by running, not by reading. Exit statuses `0` (clean
    input), `1` (findings) and `2` (no arguments) through both the
    console script and `python3 -m tiredize`; `--help` exits `0` with
    an empty stderr; `--bogus x` and `--rules` with its value missing
    both exit `2`. All three configuration faults, each exiting `1`
    with the message on stderr — including the line the README quotes
    at `README.md:250`, which is byte-for-byte what the tool prints:
    `error: Rule 'line_length': unknown configuration key
    'max_length'. Accepted keys: exclude, maximum_length.` The
    required/optional claims: `tabs: {}` still flags a tab and
    `trailing_whitespace: {}` still flags trailing whitespace, so
    both "forbidden when the key is omitted" rows are right;
    `links: {validate: false}` is accepted and exits `0`, so the
    present-not-truthy paragraph is right; `elements: {}` and
    `links: {}` both fail with "required configuration key ... is
    missing", so both `Yes` rows are right. Every YAML example in the
    README was extracted from the file and run as a rules file — all
    seven are accepted under the new validation, so none of the
    examples was falsified by criterion 9. The two schema examples
    were run against a document built to match and both exit `0`.
    Stream parity checked by diff on a configuration-error run:
    stdout and stderr byte-identical across the two entry points.

    The Custom Rules skeleton was extracted from the README
    programmatically and executed rather than read. It imports
    cleanly, `validate()` returns `[]` for a good config, and it
    raises all three documented `ValueError`s with the rule id and
    the offending key. I also appended its directory to
    `tiredize.linter.rules.__path__` and confirmed `discover_rules()`
    finds it and `run_linter()` surfaces its configuration errors
    unchanged, so the skeleton is a working rule and not just
    plausible-looking code. Finding 2 is a gap in what the prose
    explains, not a defect in the code it shows.

    Verified by reading, against `tiredize/cli.py`,
    `tiredize/__main__.py`, `tiredize/linter/utils.py`,
    `tiredize/linter/engine.py`, `tiredize/linter/rules/*.py` and
    `tiredize/markdown/types/document.py`. The `Required` column
    matches `_REQUIRED_KEYS` in all six rule modules, checked module
    by module rather than sampled. The runtime-error list at
    `README.md:139-142` is exactly the set `cli.py:133-199` catches.
    The status table matches every return in `main()`. The five type
    names at `README.md:437-438` match `_CONFIG_TYPE_CHECKS` at
    `utils.py:19-28`. The element-name table at `README.md:378-391`
    matches `_ELEMENT_MAP` name for name, all twelve. Both in-page
    anchors resolve to real headings, and all three specification
    links point at files that exist.

    Full document reviewed, not only the changed sections. I read the
    README end to end and looked specifically for preexisting wording
    the change contradicts. The only other exit-status claim in the
    file was the "nonzero exit code" sentence, which step 8 replaced;
    no other section mentions module invocation, abort behaviour or
    rule-key handling. Installation, the parser and frontmatter
    Features paragraphs, the two Configuration examples and the
    element-name table are all untouched by this change and accurate.

    Triage observation, not acted on and no fix requested. I assessed
    step 8's Features-section observation rather than repeating it,
    and it is correct: `README.md:26-28` says built-in rules "cover
    line length, tab usage, trailing whitespace, and link
    validation", omitting `unicode` and `elements`, both of which
    have full reference subsections. `git show main:README.md` has
    the identical sentence, and this branch adds and removes no
    rules, so the omission is pre-existing and not falsified here —
    step 8 was right to leave it. I add one thing to the record: the
    Features paragraph is now the only place in the README that
    enumerates the built-in rules without the `Required` column's
    account of them, so a reader who stops at Features still gets a
    four-rule picture of a six-rule tool. That is an argument for
    fixing it eventually, not for folding it into this branch.

    Beyond it I found no fourth README site this change falsified.
    Per the PM's routing, if I had, I would record it here rather
    than request a fix; I have nothing to record.

    Both findings are inside the three sites and route to step 8. No
    other file needs an edit: the code is not implicated, and neither
    specification is — `linter.md` is silent on `_RULE_ID`'s
    relationship to the filename too, but that is a contributor
    document confirmed accurate at step 7 and outside this step's
    remit.

    Action: @program-manager — request for edit

### 2026-09-06T17:00:00+00:00

Author: program-manager

    Step 9 iteration 1 landed at `5e3907f` and raised one edit request
    covering two findings. Both sit inside the three README sites step 8
    already owns, so the whole request routes back to step 8, revision
    mode, with no split and no new scope. Frontmatter set back to
    `status: in-progress`, `step: user-documentation`,
    `assignee: ghostwriter`. This is iteration 2 of the documentation
    review loop, which is capped at 5.

    Finding 1 — `README.md:114-116`, in the Usage section, site 1. The
    output sentence says violations print "followed by" a
    `no issues found.` line for the clean files, which asserts an order
    the tool does not produce: `cli.py:129-208` handles one path at a
    time, so the two kinds of line interleave in argument order. The
    reviewer measured it. The second half of the finding is that a file
    with violations never also gets a clean line (`cli.py:205-208` is
    either/or), so the sentence can be read as promising a per-file
    summary that never arrives.

    Finding 2 — `README.md:401-440`, the Custom Rules section, site 3.
    The skeleton declares `_RULE_ID` but nothing explains it: the
    constants comment describes only two of the three names, and the
    prose covers `validate_config()`, the required-versus-optional
    principle, the type names and the empty-`_ALLOWED_KEYS` case without
    ever saying what `_RULE_ID` is for. It is a hand-written string the
    engine never reads — the rule id the engine uses is derived from the
    module filename (`rules/__init__.py:63-72`, `engine.py:70`), which
    `README.md:450` already says — and it surfaces only in
    `validate_config()`'s error messages (`utils.py:160-180`). Set it to
    anything but the filename and a reader's configuration errors are
    reported against a rule id that is not in their rules file, while
    findings from the same rule carry the filename.

    Neither finding is a dispute about scope and neither asks step 8 to
    touch a fourth site. Step 9 confirmed both constraints were honoured
    — errors-abort is written as a property of the tool with a
    console-script example, and `python -m tiredize` appears exactly once
    and only as a conditional — and confirmed step 8's judgment that the
    Features section's four-rule list is pre-existing on `main` rather
    than falsified by this branch. It found no fourth site. That ground
    is settled and step 8 does not re-derive it.

    Scope of this revision: the two findings and nothing else. The rest
    of the README was verified accurate against the implementation by
    step 9, including all nine YAML examples and the Custom Rules
    skeleton, both executed rather than read. Step 8 may of course reject
    a finding it believes wrong, with
    `Action: @program-manager — disputed edit`, which stops the loop for
    the user rather than being settled here.

    All ten acceptance criteria stay ticked. On step 8's return the loop
    goes to step 9 again, iteration 3 of 5.

### 2026-09-06T18:00:00+00:00

Author: ghostwriter/software-engineering

    Step 8, user documentation, revision mode, iteration 2. Both of
    step 9's findings applied. `README.md` is the only file changed
    besides this Comments section — no code, no tests, nothing under
    `.context/specifications/`, and no other issue section. No
    acceptance criterion was ticked or unticked; all ten stay as the
    PM left them. No knowledge files were loaded, for the reason
    given at 2026-09-06T14:00:00+00:00: `AGENTS.md` maps none to the
    `user-documentation` step and the issue's frontmatter
    `knowledge` field is empty. All sections of the issue are present
    and complete per `templates/ISSUE.md`.

    Finding 1 — the output paragraph in the Usage section. The
    sentence now reads:

        For each file, in the order the paths were given, the command
        prints that file's findings to stdout as
        `file:line:col: [rule_id] message`, or a single
        `file: no issues found.` line if the file produced none.
        Runtime errors go to stderr as `error: <message>`.

    That is step 9's suggested wording with two departures, both
    deliberate.

      - "findings" rather than "rule violations". The either/or half
        of the finding is only true of findings in general. `cli.py`
        prints and counts `all_results`, which holds lint violations,
        markdown schema mismatches and frontmatter schema violations
        alike, and the clean line at `cli.py:205-208` is suppressed by
        any of them. Ran it: a markdown-schema mismatch prints
        `intro.md:1:0: [schema.markdown.unexpected_section] Unexpected
        section 'Intro'` — the same `file:line:col: [rule_id] message`
        shape — and that file gets no `no issues found.` line. Written
        as "rule violations", the replacement sentence would promise a
        clean line for a file whose only finding came from a schema,
        which would be a new inaccuracy in place of the old one. The
        term is defined in bold twenty lines below, under
        `### Exit status`, so it is not being introduced cold.
      - "in the order the paths were given" rather than "in the order
        given", which names what the order is of.

    Everything else is step 9's: the per-file grouping, the either/or,
    and the final stderr sentence left untouched.

    Finding 2 — `_RULE_ID` in the Custom Rules section. Two edits, as
    step 9 proposed. The comment above the constants was widened from
    two of the three names to all three:

        # The name this rule reports configuration errors under, every
        # key it accepts mapped to its type, and the subset it requires.

    And a paragraph was added to the prose, immediately after the
    `validate_config()` paragraph rather than at the end of the
    section — `_RULE_ID` is an argument to that call and matters only
    for its messages, so it belongs where the messages are being
    discussed:

        `_RULE_ID` names your rule in those messages, and it is the
        only place the rule's ID is written by hand: the engine never
        reads it, and derives the ID it stamps on findings from the
        module filename. Keep the two equal. Set `_RULE_ID` to
        anything else and a configuration mistake is reported against
        an ID that appears nowhere in your rules file, while findings
        from the same rule carry the filename.

    This is step 9's substance in my own words. Its suggested sentence
    — "`_RULE_ID` names the rule in `validate_config()`'s error
    messages; keep it equal to the module filename, which is the ID
    the engine uses and the one readers write in their rules file" —
    is accurate, and I departed from it only for register and for
    consequence. The README's Custom Rules section addresses the
    reader as "you" throughout ("your validation logic here", "the
    convention is yours to keep"), so "readers" became "your"; and the
    section's habit, established by the `validate_config()` paragraph
    above it, is to state the failure a convention prevents rather
    than only the convention. Hence the last sentence, which is what a
    reader would otherwise discover from a confusing error message.

    Verified by running, not taken from step 9's account or from the
    routing.

      - The interleaving. With `intro.md` and `guide.md` clean and
        `bad.md` over an 80-character limit, `tiredize --rules
        rules.yaml intro.md bad.md guide.md` prints `intro.md: no
        issues found.`, then the `bad.md` violation, then `guide.md:
        no issues found.`, and exits `1`. Identical through `python3
        -m tiredize`. Reversing the arguments to `bad.md intro.md`
        reverses the output, which is what makes it argument order and
        not coincidence. `bad.md` gets no clean line in either run.
        Checked the stream split separately: all four lines are on
        stdout and stderr is empty.
      - The `_RULE_ID` divergence, reproduced rather than reasoned
        about. I wrote the README skeleton into a module named
        `my_rule.py`, set `_RULE_ID = "wrong_name"`, appended its
        directory to `tiredize.linter.rules.__path__` and ran it
        through `run_linter`. Findings came back with
        `rule_id='my_rule'`; the configuration errors read `Rule
        'wrong_name': unknown configuration key 'max_count'.` and
        `Rule 'wrong_name': required configuration key
        'maximum_count' is missing.` One rule, two different IDs, and
        only the filename appears in the rules file. That is the
        failure the new paragraph describes.
      - The skeleton after my edit. Extracted from `README.md`
        programmatically and run the same way: `discover_rules()`
        finds `my_rule`, `validate()` returns `[]` for a good config,
        and the three `ValueError`s now all name `my_rule` — the ID
        the reader writes in their rules file. My change to the
        comment did not disturb it.

    Verified by reading, for the facts behind the wording:
    `cli.py:129-208` for the per-path loop and the either/or at
    `205-208`; `utils.py:152-180` for the three messages and the
    `rule_id` argument that labels them; `rules/__init__.py:63-73`
    and `engine.py:68-71` for the ID actually stamped on results.

    No fourth site. The two edits are confined to the two paragraphs
    step 9 named, and I checked what they touch: "findings" is used at
    its established meaning and defined below; `README.md:450`'s "The
    rule ID is derived from the module filename" is what the new
    paragraph points at rather than something it contradicts. Nothing
    else in the README describes stdout ordering or `_RULE_ID`. The
    Features-section observation from 2026-09-06T14:00:00+00:00,
    which step 9 assessed and confirmed pre-existing on `main`, stays
    where it is — not acted on here.

    No action tag raised. Nothing was disputed: both findings are
    correct, and I confirmed both against the running tool before
    applying either.

### 2026-09-06T19:00:00+00:00

Author: program-manager

    Step 8's revision landed at `42df038`. Routing back to step 9,
    documentation review, iteration 3 of 5. Frontmatter set to
    `status: in-review`, `step: documentation-review`,
    `assignee: proofreader`.

    Both findings were applied and neither was disputed. The `README.md`
    diff is +13/-5 across two hunks, exactly the two sites step 9 named:

      - The Usage output paragraph now reads "For each file, in the order
        the paths were given, the command prints that file's findings to
        stdout as `file:line:col: [rule_id] message`, or a single
        `file: no issues found.` line if the file produced none." The
        stderr sentence after it is untouched.
      - The Custom Rules constants comment now covers all three names,
        and a new paragraph after the `validate_config()` paragraph says
        what `_RULE_ID` is for, that the engine never reads it, that it
        must equal the module filename, and what diverging costs.

    Step 8 departed from step 9's suggested wording in two places and
    recorded why. Both are the reviewer's to accept or reject at this
    iteration rather than the PM's to settle:

      - It wrote "findings" where step 9 suggested "rule violations",
        because the either/or is true of findings in general — `cli.py`
        prints and counts `all_results`, which carries markdown and
        frontmatter schema findings alongside lint violations, and any of
        them suppresses the clean line. Step 8 reports running a
        markdown-schema mismatch to confirm it takes the same
        `file:line:col: [rule_id] message` shape and suppresses the clean
        line. The narrower word would have introduced a fresh inaccuracy
        in place of the corrected one.
      - It wrote the `_RULE_ID` paragraph in its own words for register,
        the section addressing the reader as "you" throughout, and named
        the failure the convention prevents rather than only the
        convention.

    Scope of this iteration. Step 9's iteration 1 verified the rest of
    the README accurate against the implementation, executed all nine
    YAML examples and the Custom Rules skeleton, confirmed both prose
    constraints honoured, confirmed the Features-section observation
    pre-existing on `main`, and found no fourth site. That ground is
    settled and is not re-derived. What this iteration checks is the two
    corrected passages, the two wording departures, and whether the
    revision introduced anything new — including whether the edited
    Custom Rules skeleton still runs.

    The fourth-site rule still stands: if this iteration finds a README
    site this change falsified beyond the three in scope, it records it
    as a triage observation and does not request a fix. All ten
    acceptance criteria stay ticked.

### 2026-09-06T20:00:00+00:00

Author: proofreader/software-engineering

    Documentation review, iteration 3. Verdict: clean. Both of
    iteration 1's findings are discharged, both of step 8's wording
    departures are accepted, the revision introduced nothing new, and
    I found no fourth site. No action tag raised and nothing routes
    anywhere.

    All sections of the issue are present and complete per
    `templates/ISSUE.md`. No acceptance criterion was ticked or
    unticked; all ten stay as the PM left them. This comment is the
    only change to the issue and `README.md` is untouched.

    The standard I applied, stated rather than left implicit. No
    knowledge files were loaded: `AGENTS.md` maps none to the
    `documentation-review` step and the issue's frontmatter
    `knowledge` field is empty, so I worked from my base function.
    Accuracy I judged against the code and the running program. Prose
    quality I judged against the README's own established voice,
    vocabulary, wrapping (prose to 72 columns) and table conventions
    — the standard there is mine, not a knowledge file's. The
    orchestrator is reporting the mapping gap to the PM separately.

    Finding 1 discharged — `README.md:114-117`. The paragraph now
    reads "For each file, in the order the paths were given, the
    command prints that file's findings to stdout as
    `file:line:col: [rule_id] message`, or a single
    `file: no issues found.` line if the file produced none." Both
    halves of the old error are gone: the false "followed by"
    ordering, and the implied per-file summary. Measured, not read.
    With `intro.md` and `guide.md` clean and `bad.md` over an
    80-character limit:

        $ tiredize --rules rules.yaml intro.md bad.md guide.md
        intro.md: no issues found.
        bad.md:3:80: [line_length] Line exceeds maximum length of 80 (120 found).
        guide.md: no issues found.

    Reordering the arguments to `bad.md intro.md guide.md` reorders
    the output identically, which is what makes it argument order
    rather than coincidence, and `bad.md` gets no clean line in
    either run. All three lines are on stdout; stderr is empty.
    Identical through `python3 -m tiredize`. The stderr sentence at
    `README.md:117` is unchanged and still correct.

    Finding 2 discharged — `README.md:406-407` and `434-440`. The
    constants comment now covers all three names rather than two, and
    the new paragraph says what `_RULE_ID` is for, that the engine
    never reads it, that it must equal the module filename, and what
    diverging costs. Every clause checked against the code:
    `grep -rn "_RULE_ID" tiredize/` shows the constant is passed to
    `validate_config()` and read nowhere else, in all six built-in
    rules; `rules/__init__.py:63-73` derives the id from the module
    name and `engine.py:70` stamps it onto every result with
    `replace(res, rule_id=rule_id)`. All six built-ins keep
    `_RULE_ID` equal to their filename, so "Keep the two equal"
    documents the convention the codebase actually follows rather
    than inventing one.

    The edited skeleton still runs — extracted from `README.md`
    programmatically and executed, not read. `discover_rules()` finds
    it as `my_rule` after appending its directory to
    `tiredize.linter.rules.__path__`, `validate()` returns `[]` for a
    good config, and all three `ValueError`s name `my_rule`: unknown
    key, missing required key, wrong-typed value. The widened comment
    disturbed nothing. I also reproduced the failure the new
    paragraph describes rather than reasoning about it: with
    `_RULE_ID = "wrong_name"` in a module still named `my_rule.py`,
    the configuration error reads `Rule 'wrong_name': unknown
    configuration key 'max_count'.` while a finding from the same
    rule comes back with `rule_id='my_rule'` — the engine's `replace`
    overwrites even a rule_id the rule set itself. One rule, two IDs,
    and only the filename is the key in the rules file. The paragraph
    is accurate in both directions.

    Departure 1 accepted — "findings" rather than "rule violations".
    Step 8's reasoning is correct and I verified it rather than
    taking it. A markdown-schema mismatch prints
    `intro.md:1:0: [schema.markdown.unexpected_section] Unexpected
    section 'Intro'` and a frontmatter violation prints
    `fmbad.md:1:0: [schema.frontmatter.value_not_allowed] Field
    'status' value 'bogus' is not allowed. ...` — both the same
    `file:line:col: [rule_id] message` shape, both counted in
    `all_results`, and a file with either gets no `no issues found.`
    line. Written as "rule violations" the sentence would promise a
    clean line for a file whose only finding came from a schema,
    which is a fresh inaccuracy in place of the corrected one. My
    suggested wording was the narrower and worse one; step 8 was
    right to depart.

    On whether "findings" is used before it is defined: it is, by
    nineteen lines, and I am not raising it. The word is already used
    twice in the status table at `README.md:127-128` ahead of the
    bold definition at `134`, so the new use follows a pattern the
    section had already established and iteration 1 passed. The
    README's vocabulary is coherent, which is the substantive point:
    "findings" is the umbrella term everywhere output and status are
    described (`115`, `127`, `128`, `137`, `146`, `155`), and
    "violation" is used only rule-locally (`284`, `298`, `361`). The
    reader also meets `no issues found.` in the same sentence, and
    the definition arrives in the very next subsection.

    Departure 2 accepted — the `_RULE_ID` paragraph in step 8's own
    words. It carries the whole substance of my suggested sentence
    and adds the consequence. The register argument holds: the
    section addresses the reader as "you" throughout, and the
    `validate_config()` paragraph directly above it ends on the
    failure the convention prevents, so the new paragraph matches its
    neighbour's shape. Placement after that paragraph rather than at
    the end of the section is right too — `_RULE_ID` is an argument
    to that call and matters only for its messages.

    Two things I considered and am not raising, recorded so the next
    reviewer can see they were examined rather than missed.

      - `README.md:434-435`, "it is the only place the rule's ID is
        written by hand". A reader also writes the ID by hand as the
        top-level key of their rules file, which the same paragraph
        acknowledges four lines later. Read as scoped to the rule
        module — which the colon's justification, entirely about the
        engine and the module filename, makes the natural reading —
        it is true, and the paragraph supplies its own correction
        before a reader could act on the looser one. Imprecision, not
        a defect, and not worth an iteration.
      - `README.md:114`, "For each file". A run that hits a runtime
        error does not reach every file. But the sentence is
        distributive about what a processed file yields rather than a
        promise that every file is reached, and `README.md:139-156`
        states the abort and its consequence explicitly twenty-five
        lines below in the adjacent subsection. The old sentence made
        the same implication.

    No contradiction with preexisting wording. `README.md:458`, "The
    rule ID is derived from the module filename (e.g., `my_rule.py`
    produces rule ID `my_rule`)", is what the new paragraph points
    at, not something it contradicts — same fact, and `458` adds the
    example and the `config` dict. The new prose wraps to 72 columns
    like its neighbours (longest new line, 69) and the constants
    comment stays inside the code block's own width.

    Iteration 1's settled ground confirmed unmoved rather than
    re-derived. `git diff 5e3907f HEAD -- README.md` is the two hunks
    and nothing else, +13/-5, so the nine YAML examples, the
    element-name table, the `Required` columns, the status table, the
    runtime-error list and the type names all stand as verified at
    iteration 1. I spot-checked the two constraints anyway because
    they are cheap: `grep -n "python -m" README.md` still returns
    exactly one line, `78`, the conditional; `python3 -m` appears at
    `71`; errors-abort at `README.md:146` is still written as a
    property of the tool with the console-script example at `151`,
    and the run still prints the error, reports the earlier file,
    never touches `guide.md` and exits `1`. Statuses `0`, `2` and
    `--help`'s `0` re-confirmed on the console script.

    No fourth site. Nothing else in the README describes stdout
    ordering or `_RULE_ID`. The Features-section observation from
    2026-09-06T14:00:00+00:00 stands where iteration 1 left it —
    pre-existing on `main`, not falsified by this branch, and not
    acted on here.

### 2026-09-06T21:00:00+00:00

Author: program-manager

    Step 9 iteration 3 came back clean at `5947a35` and the documentation
    review loop closed at 3 of 5. No action tag was raised at that
    iteration, and none is outstanding anywhere on this issue.

    The documentation track is complete. Three README sites were revised
    across two step-8 passes — the Usage section, the rule reference, and
    Custom Rules — and reviewed twice by the proofreader. Iteration 1
    raised two findings; step 8 applied both without dispute; iteration 3
    confirmed both discharged, accepted both of step 8's departures from
    iteration 1's suggested wording, and found nothing new. `README.md`
    is the only non-issue file the track touched: +144/-31 against `main`.

    Both prose constraints held and were verified by the reviewer rather
    than taken on the writer's word. Errors-abort is written as a
    property of the tool with a console-script example, not as a `-m`
    change. `python -m tiredize` appears exactly once in the file, as a
    conditional for readers whose `python` is the right interpreter; the
    examples use `tiredize` and `python3 -m tiredize`.

    No fourth README site was falsified by this change. Step 8 recorded
    one triage observation — the Features section listing four built-in
    rules where the reference documents six — and step 9 independently
    confirmed it pre-existing on `main`, so no fourth scope exception is
    needed and none was taken.

    Frontmatter is left as step 9 left it. Step 10, closeout, is the
    third user approval gate and is the PM's to route with the user; the
    orchestrator stops here rather than entering it.

    One process observation, carried to the PM rather than raised as a
    tag by either agent. `AGENTS.md`'s knowledge map has no entry for
    `user-documentation` or `documentation-review`, while both step files
    name `markdown-style` and `ai-prose-hygiene` in their Inputs and both
    files exist in the configuration repository. The issue's frontmatter
    `knowledge` is `[]`, so both agents ran on their base function alone
    and drew their standard from the README's own conventions. Both said
    so explicitly rather than letting the gap pass silently. Worth
    closing in `AGENTS.md` before the next issue runs a documentation
    track.

### 2026-09-06T21:00:00+00:00

Author: program-manager

    The documentation review closed clean at iteration 3 of 5. Every
    step of the pipeline has now run. Routing to step 10, closeout.

    Three items for the workflow owner to pick up, all recorded in
    Comments above and none acted on:

      - `Action: @workflow-owner — process improvement` from step 6.
        `knowledge/specifications.md` gives no guidance for authoring a
        deliberately partial specification, which criterion 8 required,
        and its prohibition on TODO-style prose leaves no sanctioned
        way to say a section does not exist yet. Step 7 met the same
        gap from the reviewing side and declined to raise a duplicate.
      - The `AGENTS.md` knowledge-mapping gap. Its `knowledge:` block
        has no entry for `user-documentation` or `documentation-review`,
        so the ghostwriter and the proofreader ran on base function
        alone, with the issue's `knowledge` field empty. Both step files
        name `markdown-style` and `ai-prose-hygiene` in their Inputs and
        both files exist, so this is a missing mapping, not missing
        knowledge. Both agents disclosed it rather than letting it
        pass. The prose standard applied to this README was therefore
        the agents' own judgment; it held up, but nothing in the
        configuration guaranteed it would. This is a defect in the
        project's own configuration, outside the ten criteria.
      - The README Features section, a follow-up candidate. It says the
        built-in rules "cover line length, tab usage, trailing
        whitespace, and link validation" — four, where the reference
        documents six. Both step-8 and step-9 agents verified it is
        pre-existing on `main` and correctly left it alone. Step 9's
        addition: Features is now the only enumeration of the built-in
        rules that does not account for the new Required column, so a
        reader who stops there gets a four-rule picture of a six-rule
        tool. An argument for a separate issue, not for folding in.

    Three scope exceptions were ratified by the user during this issue
    and are recorded at 05:00, 06:00 and 13:00 on 2026-09-06. Closeout
    should account for them as ratified rather than as scope drift.

    All ten acceptance criteria are ticked. The Open Questions section
    should be confirmed fully resolved as part of the checklist.

### 2026-09-06T22:00:00+00:00

Author: workflow-owner/software-engineering/git

    Closeout. Verdict: the branch is complete and coherent against all
    ten acceptance criteria, every pipeline step is accounted for in git
    history and in Comments, and no discrepancy blocks acceptance. The
    branch is handed to the user for approval gate 3. Nothing was
    pushed, merged or rebased, and the issue stays where step 9 left it
    — not moved to `completed/`, `status` not set to `done`. Those are
    the PM's after the user accepts.

    Everything below was observed on this branch rather than carried
    over from the reports it checks.

    Issue validated against `templates/ISSUE.md`. All five body sections
    present in template order — Summary, Acceptance Criteria, Design
    Decisions, Open Questions, Comments. Frontmatter carries all nine
    fields. The one Open Question, the silent unknown-rule-configuration
    key raised at step 2, is marked resolved in place with the decision
    recorded and its design carried into Design Decisions under
    "Validating rule configuration". No question is left open. All ten
    criteria are ticked and I neither ticked nor unticked any.

    Step verification. Every step has at least one commit recording its
    work, and every commit on the branch belongs to a step or to a PM
    routing entry. 48 commits, working tree clean.

      - Step 1, scoping. `1094ba8`, `326b2ff`, `8f716e1`, `e78da7e`,
        `184062f`, `4d16d39`, `7ba1424`, `c827865`, `5878425`. Two
        approval gates passed; the criteria grew from five to ten across
        them.
      - Step 2, acceptance test design. `204bbeb`, `d1adfe5`, `79db0fb`,
        `019233b`, `3cbaeb7`. Re-entered once, for criteria 9 and 10
        only, with the first pass's 23 tests untouched.
      - Step 3, implementation. `610c27a`, `c9a0d49`, `4cb8cb4`,
        `ea889a5`, `14e7d10`, plus the revision at `5653386`.
      - Step 4, code and test review. `84f32be` (iteration 1, two
        findings), `63ef6b0` (iteration 2, clean). Two iterations of
        five.
      - Step 5, acceptance verification. `8e91d99`, pass on the first
        pass. One iteration of five.
      - Step 6, technical reference. `82f8d75`, `03a6cd6`, `08b1cab`,
        plus the scoped revision at `50c5209`.
      - Step 7, architecture review. `76ed4f0` (iteration 1, one
        reference finding), `c91c312` (iteration 2, clean). Two
        iterations of five.
      - Step 8, user documentation. `a643275`, `42df038`.
      - Step 9, documentation review. `5e3907f` (iteration 1, two
        findings), `5947a35` (iteration 3, clean). Three iterations of
        five.
      - Step 10, closeout. This comment.

    The conditional steps, checked against the workflow's conditions
    rather than against the pipeline's account of them.

      - Step 6 was not a no-op and correctly was not. Three contracts
        changed — the exit status of `python -m tiredize`, `main()`'s
        abort semantics, and the rule-module convention — so the
        architect authored `.context/specifications/cli.md` and updated
        `.context/specifications/linter.md`. Both exist on the branch;
        `cli.md` is new at 176 lines and `linter.md` is +193.
      - Steps 8 and 9 ran, and ran only because step 7 required them.
        The decision is logged with its reasoning at
        2026-09-06T08:00:00+00:00, made by the technical-architect and
        not by the PM or the scoping seed, and it names three
        user-visible changes that nothing user-facing documented. Step 9
        ran because step 8 ran. Both conditions are satisfied in the
        right order by the right role.

    Final deliverable, confirmed criterion by criterion. I drove both
    entry points by hand rather than reading the tests.

      1. Exit status equals `main()`'s return. `0` on a clean document,
         `1` on a `line_length` finding, `2` with no arguments, `0` on
         `--help`. All through `python3 -m tiredize`.
      2. `tiredize/__main__.py` is `raise SystemExit(main())`, the
         preferred idiom, with a docstring explaining why the wrapper is
         needed.
      3. `tests/test_main_module.py` spawns subprocesses and asserts all
         three statuses; the file is 49 items across five classes with
         zero `@pytest.mark.skip` markers, and all 49 pass.
      4. `git diff main..HEAD -- tests/test_cli.py` is exactly two
         hunks: `max_length` to `maximum_length` in
         `test_valid_document_passes_rules`, which criterion 4 permits
         by name, and one added test. No other existing test in the file
         is edited or deleted.
      5. Parity held on six argument lists spanning clean input,
         findings, a runtime error, the usage error, an argparse error
         and `--help` — exit status, stdout and stderr byte-identical
         between `python3 -m tiredize` and the console script at
         `/home/admin/.local/bin/tiredize` on every one.
      6. A missing document followed by a clean one prints the error to
         stderr, never reports the later path, and exits `1`.
      7. `.context/schemas/issue-frontmatter.yaml` lists
         `program-manager` and no longer lists `PM`;
         `context-process-migration.md` carries
         `assignee: program-manager`; no `assignee: PM` survives. All
         ten files in `.context/issues/` validate clean against both
         project schemas together, exit `0`.
      8. `.context/specifications/cli.md` exists and carries the
         template's sections in the template's order — Overview,
         Contracts and Interfaces, File Layout, one domain section
         (Exit Status Contract), Design Decisions — with the status
         table, the findings-continue and errors-abort semantics, and
         the corrected `--help` treatment.
      9. All three fault states are runtime errors that abort, each
         naming the rule id and the offending key on stderr and exiting
         `1`; an omitted optional key exits `0`.
     10. Verified on all six built-in rules individually, not sampled:
         `elements`, `line_length`, `links`, `tabs`,
         `trailing_whitespace` and `unicode` each reject an unknown key
         with their own accepted-key list. `linter.md`'s Rule Module
         Convention carries requirement 4 with a worked skeleton, and
         the new Rule Configuration Validation section carries the fault
         states, the type vocabulary and the per-rule key table.

    The three ratified scope exceptions all landed on the branch as
    described, and each is accounted for as a ratified decision rather
    than as drift.

      - `linter.md`'s File Layout now lists all six rule modules plus
        `_elements.py`, so it no longer contradicts the section added
        two headings below it.
      - `.context/PROJECT.md`'s CLI entry carries
        ``Spec: `specifications/cli.md`.`` in the form the four other
        subsystem entries use.
      - `README.md`'s Custom Rules section teaches `_RULE_ID`,
        `_ALLOWED_KEYS`, `_REQUIRED_KEYS` and the `validate_config()`
        call.

    Closeout checklist.

      - [x] Issue file updated with final design decisions, all open
            questions resolved, and every acceptance criterion checked
            off. Design Decisions carries eleven subsections including
            the two the folded-in criteria required; the single Open
            Question is resolved in place; all ten criteria ticked.
      - [x] Specification updated to reflect the accepted change.
            Contracts changed in two subsystems, and step 6's output is
            on the branch: `cli.md` new, `linter.md` updated in four
            places. Step 7 checked both against the code path by path.
      - [x] User-facing documentation verified accurate against the
            implementation. Three README sites revised, +144/-31 against
            `main`, reviewed twice by the proofreader, who executed the
            YAML examples and the Custom Rules skeleton rather than
            reading them.
      - [x] Decisions whose reversal would materially change a subsystem
            migrated into the relevant specification. "Errors abort the
            run" is in `cli.md`'s Design Decisions with the
            batch-validator alternative recorded as the alternative;
            "Validating rule configuration" is split across five entries
            in `linter.md`. The fix idiom is recorded as contract rather
            than as decision, correctly — it changes no behavior. What
            was deliberately not migrated is test-suite and process
            history, which belongs to no subsystem.

    Completion report.

    **Problem.** `tiredize/__main__.py` called `main()` and discarded
    its return value, so `python -m tiredize` always exited `0` —
    findings, missing files, bad schemas and the usage error alike. The
    module invocation could not signal failure and was unusable as a CI
    or pre-commit gate, which is the use the README pitches the tool at.
    Two further defects were folded in on the user's direction: the
    exit-code contract was inconsistent, because a missing input
    document set the status and continued while configuration errors
    aborted; and every rule-configuration accessor returned `None` for a
    key that was missing and for one holding a wrong-typed value alike,
    so a typo in any rule's configuration silently switched that rule
    off across the whole tool. This repository's own test suite shipped
    an instance of it.

    **Solution.** `tiredize/__main__.py` now raises `SystemExit(main())`
    with a docstring explaining why module execution needs what the
    console script gets from its generated wrapper. `main()`'s
    `FileNotFoundError` handler returns instead of continuing, so the
    rule is uniform: errors abort, findings continue — a change that
    lands on the console script too, not only on `-m`.
    `validate_config(config, allowed, required, rule_id)` is new in
    `tiredize/linter/utils.py`; each of the six built-in rules declares
    `_RULE_ID`, `_ALLOWED_KEYS` and `_REQUIRED_KEYS` at module level and
    calls the helper as the first statement of `validate()`. Faults are
    reported in a fixed order — unknown keys, then omitted required
    keys, then wrong-typed values — with unknown keys first because a
    typo makes the other two misleading. The `Rule` dataclass and rule
    discovery are untouched, and the new `ValueError` leaves
    `run_linter()` through the exception channel the CLI already caught,
    which is why the blast radius stopped at the rules and the helper.
    `.context/schemas/issue-frontmatter.yaml` was reconciled with
    upstream so `program-manager` replaces `PM`.

    **Test summary.** Full suite 844 passed / 50 skipped / 0 failed, 894
    collected items, `flake8 tiredize tests` clean — run here, not
    carried over. All 50 skips are the pre-existing `gfm-parity` skips
    in the markdown parser tests. Across the eleven changed test files
    the test-function count goes from 216 on `main` to 304, +88.

      - `tests/test_main_module.py`, new: 39 functions / 49 items in
        five classes. `TestExitStatus`, `TestStreamParity`,
        `TestIssueAssigneeVocabulary` and `TestRuleConfigurationValidation`
        are the 43-item black-box acceptance tier written at step 2
        against the Public Contract; `TestModuleExecution` is the
        six-item white-box tier added at step 3, driving the module body
        through `runpy.run_module` for coverage the subprocess tests
        cannot reach. Zero skip markers.
      - `tests/linter/test_utils.py`: 49 to 70 functions, 74 items —
        `validate_config`'s three fault states, ordering when faults
        coexist, one wrong type per declared type, bool/int confusion
        both ways, `None` values, empty collections and strings,
        non-ASCII keys and values, no-mutation and idempotency.
      - `tests/linter/rules/test_loader.py`: 6 to 11 functions, 29
        items — parametrized guards over every discovered built-in rule,
        so a rule module added without the declaration fails a test.
      - `tests/test_cli.py`: one test added
        (`test_missing_document_aborts_remaining_paths`) and one
        repaired under criterion 4's carve-out.
      - The six rule test files and `test_engine.py`: per-rule
        configuration sections, and seven pre-existing tests rewritten
        from asserting the silent no-op to asserting the error. Each
        asserts strictly more than the test it replaced.

    **Coverage.** 99% overall, 1553 statements, 11 uncovered — measured
    here and matching step 5's figure exactly. Changed source files:
    `tiredize/__main__.py` 100% (was 0%), `tiredize/linter/utils.py`
    100%, `rules/tabs.py`, `rules/trailing_whitespace.py` and
    `rules/links.py` 100%, `rules/unicode.py` 98% (line 56),
    `rules/elements.py` 97% (62), `rules/line_length.py` 95% (55-58),
    `cli.py` 98% (59, 213). Every uncovered line is a pre-existing gap
    in code this issue did not touch: the range-merge branches in
    `line_length` and `unicode`, the zero-length-element `continue` in
    `elements`, the empty-YAML `return {}` and the
    `if __name__ == "__main__"` guard in `cli.py`. The remaining
    uncovered lines in the report — `engine.py:64`, `section.py:167`,
    `table.py:61`, `markdown_schema.py:173` — are in files this branch
    does not modify. No new uncovered line was introduced, and the one
    file that had a visible hole no longer does.

    **Review — incorporated.** Four findings across four review gates,
    all fixed, none disputed.

      - Step 4 iteration 1, finding 2: the orphaned `Config gating`
        banner in `tests/linter/rules/test_unicode.py`, left behind by
        step 3's own edit. Routed back to step 3 and deleted at
        `5653386`.
      - Step 4 iteration 1, finding 1: `README.md:237` telling readers
        that omitting `unicode.allowed` disables the rule, which
        criterion 9 turned into a runtime error. Deferred by the PM to
        step 8 rather than fixed at step 3, on the grounds that
        user-facing prose is the ghostwriter's, and landed there.
      - Step 7 iteration 1: `cli.md` listed `--help` among argparse's
        own errors and then said those exit `2`. It exits `0` and writes
        to stdout. Routed to step 6 alone — correctly, since the defect
        was in the reference and not the code — and corrected at
        `50c5209` across four sites, with the stream table gaining the
        argparse-error row that the same omission had left out from the
        other side. Step 7 iteration 2 confirmed it and only then was
        criterion 8 ticked.
      - Step 9 iteration 1: `README.md`'s output paragraph claimed
        findings print "followed by" the clean-file lines, when output
        interleaves in argument order; and the Custom Rules skeleton
        introduced `_RULE_ID` without explaining it, a hand-written
        string the engine never reads. Both applied at `42df038`, both
        with deliberate wording departures the reviewer then accepted —
        "findings" rather than "rule violations", because the narrower
        word would have promised a clean line to a file whose only
        finding came from a schema.

    **Review — not incorporated.** Nine observations were recorded
    across steps 3, 4, 5, 7 and 8 and deliberately not acted on. I
    confirmed the state of each on the branch rather than taking the
    record's word.

      - The null rule-configuration block. `line_length:` with nothing
        under it is still reported by the engine as
        `Invalid configuration for rule line_length: None`, naming the
        rule but not the required key — confirmed by running it. Raised
        at step 4 and again from the outside at step 5. Pre-existing,
        unchanged by the diff, and the contract still holds: stderr,
        exit `1`, run aborted. Step 3 recorded a deliberate decision to
        leave the non-mapping case with the engine so a second message
        for the same condition could not contradict the first. Left as
        is, and it is the likeliest real-world shape of a required key
        omitted for a single-key rule.
      - Criterion 7's recursive-versus-glob reading. Read recursively,
        "every file in `.context/issues/`" would include the 20 archived
        files in `completed/`, which do not validate. I ran them: every
        failure is a missing `workflow`, `tags` or `knowledge` field on
        a v1-format issue, not one is assignee-related, and
        `git diff main..HEAD -- .context/schemas/` is the assignee list
        alone, so those fields were already required on `main`. The
        schema's own documented usage line and the gate-2-approved
        `test_every_issue_file_validates_clean` both use the
        non-recursive `*.md` glob. The archive is outside the criterion
        on the approved reading and its state is untouched by this
        branch. Whoever finishes `context-process-migration` will meet
        it.
      - `validate_config` does not check that `config` is a mapping.
        `run_linter` already raises for that, and a second message would
        risk the contradiction criterion 9 warns about.
      - The type vocabulary is coarse: `list` and `dict` are not checked
        element-wise. Every rule that cares checks its own entries at
        value level, so nothing is unguarded, but a future rule author
        could declare `list` and forget the inner check.
      - `validate_config` declares a `str` type no built-in uses, and
        its "accepts no configuration keys" branch cannot fire for a
        built-in. Both belong to the helper's contract for custom rules
        and both are directly covered in `tests/linter/test_utils.py`.
      - The boundary enforced by prose alone. `discover_rules()`
        requires only a `validate` function, so a third-party rule that
        skips `validate_config()` reinstates the silent no-op and no
        test can catch it. This follows from the deliberate decision to
        declare key sets in the module rather than on `Rule`;
        `linter.md` states the requirement as non-optional and
        `README.md`'s Custom Rules section now tells the reader the
        same, which is the strongest instrument the chosen design
        leaves.
      - `linter.md`'s URL Validation section shows `check_url_valid`
        without its `valid_status_codes` parameter. I checked
        `utils.py:192-200`: the parameter is there and the signature in
        the specification is one argument short. Stale on `main` before
        this branch, outside step 6's scoped revision, and the only
        remaining inaccuracy I found in a specification this pipeline
        touched. It is not a defect in this change.
      - `.context/PROJECT.md` says the CLI "orchestrates three
        subsystems" and then lists four. Confirmed on the branch;
        pre-existing on `main`, and the specification-pointer addition
        at `08b1cab` correctly did not act on it.
      - `tests/linter/rules/test_loader.py:139` asserts every built-in
        rule declares at least one key, while `linter.md:94-96` says a
        rule accepting no keys still calls `validate_config()` with an
        empty `_ALLOWED_KEYS`. Both defensible — the specification
        describes the convention including custom rules, the guard pins
        the built-ins — but a future built-in with no configuration keys
        would fail a guard the specification does not mention.

    **Follow-up work.** No issues were created; these are candidates for
    the user to rule on.

      - The `AGENTS.md` knowledge-mapping gap. Its `knowledge:` block
        has no entry for `user-documentation` or `documentation-review`,
        so the ghostwriter and the proofreader ran on base function
        alone with the issue's `knowledge` field empty. Both step files
        name `markdown-style` and `ai-prose-hygiene` in their Inputs and
        both files exist in the configuration repository, so this is a
        missing mapping rather than missing knowledge. Both agents
        disclosed it in their comments rather than letting it pass, and
        both fell back to the README's own conventions. The prose held
        up under review, but nothing in the configuration guaranteed it
        would. This is a defect in the project's own configuration and
        outside the ten criteria. Worth closing before the next issue
        runs a documentation track.
      - The README Features section. It says the built-in rules "cover
        line length, tab usage, trailing whitespace, and link
        validation" — four, where the reference documents six.
        `git show main:README.md` carries the identical sentence, so it
        is pre-existing and this branch neither introduced nor worsened
        it; steps 8 and 9 both verified that independently and both
        correctly left it alone. Step 9 added the argument for fixing
        it: Features is now the only enumeration of the built-in rules
        that does not account for the new Required column, so a reader
        who stops there gets a four-rule picture of a six-rule tool.
      - Beyond those two, the nine not-incorporated observations above
        are each a candidate in their own right. The three I would put
        first, on the grounds that each is a live inaccuracy or a real
        gap rather than a recorded tension: the `linter.md` URL
        Validation signature, the null rule-configuration block's
        message, and the custom-rule boundary that only prose enforces.

    **Breaking changes.** Three, all deliberate, all named by an
    acceptance criterion, and all now documented for users rather than
    only for contributors.

      1. `python -m tiredize` exits non-zero where it previously always
         exited `0`. Anything that treated a `0` from the module
         invocation as a pass will start failing — which is the point.
      2. Runtime errors abort the run. `tiredize --rules r.yaml *.md`
         with one missing file used to report the survivors and now
         stops at the first error. This lands on the console script as
         well as on `-m`, so it is a behavior change for existing users
         who never touched module invocation.
      3. A rules file that used to run can now hard-fail. An unknown
         key, a wrong-typed value or an omitted required key is a
         runtime error that aborts. Four rules that previously returned
         no findings for an absent required key now raise. Anyone whose
         rules file carries `max_length` — the exact typo this
         repository's own suite shipped — meets it on upgrade.

    Work trail. What was built and how it evolved.

    Scoping opened at five criteria for what looked like a one-line
    propagation fix and closed at ten. Three things grew it, each a user
    decision rather than an agent's. At approval gate 1 the user chose
    "errors abort, findings continue" over the batch-validator behavior,
    having heard the argument for keeping it, which turned a pure
    propagation fix into a change to `main()` and therefore to the
    console script. The same gate folded in the `assignee: PM` schema
    fix over a recorded scope-discipline objection, and put
    `.context/specifications/cli.md` in scope, pre-empting the
    architect's step-6 judgment on whether a specification was warranted
    while leaving its content to them.

    The third growth came from the tests. Writing acceptance tests at
    step 2, the qa-engineer found that
    `tests/test_cli.py::test_valid_document_passes_rules` configured
    `max_length` where the rule reads `maximum_length`, so the test
    asserted a clean document against a rule that never ran — and that
    the defect was not local to `line_length` but structural, since
    every accessor in `utils.py` returns `None` for missing and
    wrong-typed alike. The qa-engineer stopped rather than assuming and
    raised the only open question of the issue. The user folded it in as
    criteria 9 and 10 against the PM's recommendation to split it,
    roughly doubling the issue and moving it from CLI plumbing into the
    linter engine. Step 2 was re-entered for the new criteria with the
    first pass's 23 tests untouched, and criterion 4 was amended to
    permit repairing the one test criterion 9 would otherwise break
    while criterion 4 forbade touching.

    One design question needed settling twice. An early code-shape
    heuristic classified a configuration key as required by whether it
    had a fallback default, which could not settle `elements.disallow`
    or `links.validate` — both have a default and an early return. The
    principle that replaced it — enabling a rule must never be a no-op,
    so a key is required when its absence leaves the rule inert — settled
    those two as required and settled `tabs.allowed` and
    `trailing_whitespace.allowed` as optional, since both rules still
    forbid what they exist to forbid with the key absent. Step 2 had
    deliberately built its parametrized fixtures to hold under either
    reading, which is why the classification could be settled at step 3
    without invalidating tests written before it.

    From step 3 the trail is four review gates and two revisions.
    Step 4 iteration 1 found two documentation-level defects and nothing
    in the source; the PM split the request, routing the test-scaffolding
    half back to step 3 and deferring the README half to step 8 with a
    recorded contingency for what would happen if the documentation
    track never ran. Step 5 passed on the first attempt after driving 59
    argument lists through both entry points. Step 6 wrote both
    specifications and declared two out-of-scope corrections rather than
    absorbing them, both of which the user ratified. Step 7 caught the
    one real defect in the reference — a status code, in a document
    whose whole subject is status codes, written for a reader wiring a
    CI gate — and withheld criterion 8 until step 6 fixed it. Step 9
    found two more prose defects and accepted both of step 8's departures
    from its own suggested wording, one of which prevented a fresh
    inaccuracy.

    Open questions and disputed edits. One open question, raised at step
    2 and resolved by the user as criteria 9 and 10. No edit was ever
    disputed: every finding at every gate was accepted by its producer,
    and the two wording departures at step 8 were recorded with reasons
    and accepted by the reviewer rather than escalated. No iteration cap
    was approached — the worst gate ran two of five reviews, and the
    documentation loop closed at three of five.

    Process improvement suggestions from agents. One tag was raised, at
    step 6, and step 7 met the same gap from the reviewing side and
    declined to raise a duplicate. It is summarized under process
    friction below.

    Process friction. Where effort was spent that a better-shaped
    process would not have needed. What went well is not recorded here.

    Action: @workflow-owner — process improvement

    `knowledge/specifications.md` has no guidance for authoring a
    deliberately partial specification, which is exactly what criterion
    8 required. Its structure section assumes a specification describes
    its subsystem whole, and its rule that a specification is a
    reference and not a history leaves no sanctioned way to say "this
    section does not exist yet" without the sentence reading as a TODO,
    which the same file forbids. The architect resolved it by declaring
    the partiality in the Overview as a scope boundary rather than as
    planned work and pointing the reader at the source for what is not
    covered — a reading they explicitly flagged as their own rather than
    the knowledge file's. The gap has a second half the reviewer found
    from the other side at step 7: there is no criterion for *judging* a
    partial specification either, so the standard applied at architecture
    review — does it cover what it claims, and are its silences declared
    rather than accidental — was also the agent's own. Seeding a
    specification from one issue and growing it across later ones is a
    pattern this project will hit again, and it hit it here on the first
    try. A short paragraph in `knowledge/specifications.md` on how a
    partial specification declares its own boundary, and how a reviewer
    should judge one, would close both halves.

    Action: @workflow-owner — process improvement

    `AGENTS.md`'s knowledge map has no entry for `user-documentation` or
    `documentation-review`, so both documentation-track agents ran on
    base function alone. The cost was real but small and it landed
    entirely on quality assurance rather than on rework: the ghostwriter
    and the proofreader each had to derive a prose standard from the
    README's own conventions and then say so in their comments, and the
    proofreader had to state its own review standard before it could
    apply one. Both files the step Inputs name exist in the
    configuration repository. The output held up, but it held up on two
    agents' judgment rather than on anything the configuration
    guaranteed, and the gate that would have caught a lapse is the same
    judgment. This is the one place in the run where the process did not
    give a step what its own step file says it needs.

    Action: @workflow-owner — process improvement

    Two criteria arrived after the criteria they invalidated. Criteria 9
    and 10 were folded in at approval gate 2, after step 2 had already
    written 23 tests and after criterion 4 had already promised that
    every existing test in `tests/test_cli.py` would pass unmodified —
    a promise criterion 9 then broke, forcing an amendment to carve out
    one test by name. The re-entry itself was cheap and clean, because
    step 2 is before implementation and nothing had been built yet. The
    friction is narrower: nothing in the workflow prompts a check of
    whether a newly folded-in criterion contradicts an existing one, so
    the collision was found by an agent reading carefully rather than by
    the process. A scoping step that amends criteria mid-flight is worth
    one explicit pass over the criteria it did not touch.

    Action: @workflow-owner — process improvement

    Step 4's edit request needed splitting across two steps, which the
    workflow does not describe. The gate found one test-scaffolding
    defect belonging to step 3 and one README defect belonging to a step
    8 that had not been decided on yet, and the routing rules assume a
    request routes whole to one producer. The PM handled it by splitting
    the request and recording a contingency for the case where step 7
    declined the documentation track and the deferred finding would have
    had no home. That worked, and the contingency did not fire — but it
    was invented at routing time, and a review gate finding a defect
    that belongs to a conditional step not yet decided is a shape this
    workflow will meet again whenever steps 4 and 5 precede the step-7
    documentation decision. Worth naming in the workflow rather than
    re-invented.

    No `Action: @program-manager — open question` is raised. Nothing
    discrepant enough to block closeout was found; the two places where
    the record and the branch could have parted are noted in the report
    above and neither is a defect in the delivered work.

    Handing to the PM for presentation at approval gate 3.

### 2026-09-06T23:00:00+00:00

Author: program-manager

    Approval gate 3: the user accepted the completed work. Status set to
    `done` and the issue moved to `.context/issues/completed/`.

    The branch `issues/main-module-exit-code` is not pushed, merged or
    rebased, and acceptance does not authorize any of those. Merging is
    a separate decision the user makes explicitly.

    Four follow-up candidates are recorded in the closeout report at
    2026-09-06T22:00:00+00:00 and have not been ruled on. None is a
    defect in the delivered work; all are pre-existing or configuration
    gaps found while working this issue. They are preserved here because
    this file is the only place they are written down:

      - The `AGENTS.md` knowledge-mapping gap: no entry for
        `user-documentation` or `documentation-review`, so both
        documentation-track agents ran on base function alone. A defect
        in this project's own configuration.
      - `.context/specifications/linter.md`'s URL Validation section
        shows `check_url_valid` without its `valid_status_codes`
        parameter. Stale on `main`; the only remaining inaccuracy in a
        specification this pipeline updated.
      - The README Features section lists four built-in rules where the
        reference documents six. Pre-existing on `main`, and now the
        only enumeration that does not account for the new Required
        column.
      - A null rule-configuration block is reported by the engine
        without naming the missing key. Pre-existing, contract intact,
        and the likeliest real-world shape of an omitted required key.

    Also carried forward, from the workflow owner's process friction:
    `knowledge/specifications.md` gives no guidance for authoring or
    judging a deliberately partial specification, and a review gate that
    finds a defect belonging to a conditional step not yet decided has
    no described routing. Both belong to the sibling configuration
    repository, not to this one.
