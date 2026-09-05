---
assignee: software-engineer
created: 2026-06-15
knowledge: []
priority: medium
status: in-review
step: code-and-test-review
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

- [ ] `python -m tiredize` exits with exactly the value returned by
      `tiredize.cli.main()`: `0` when all paths are clean, `1` on findings
      or runtime error, `2` on usage error
- [ ] `tiredize/__main__.py` propagates the return value of `main()` as
      the process exit status (e.g. `raise SystemExit(main())`)
- [ ] An automated test invokes `python -m tiredize` as a subprocess and
      asserts the exit status for three cases: clean input (`0`), input
      with findings (`1`), and the usage error with no arguments (`2`)
- [ ] Every test already in `tests/test_cli.py` passes unchanged, with one
      exception: `test_valid_document_passes_rules` is repaired to
      configure `maximum_length`, because criterion 9 turns its current
      `max_length` into an error. New tests may be added to that file; no
      other existing test in it may be edited or deleted
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
- [ ] An invalid rule configuration is a runtime error. All three states
      are errors: a key the rule does not accept, a key the rule accepts
      holding a value of the wrong type, and a required key omitted. Each
      prints to stderr naming the rule id and the offending key, exits
      `1`, and aborts the run per the processing semantics above. An
      omitted optional key remains legal and is not an error
- [ ] Every built-in rule validates its configuration this way, and
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
