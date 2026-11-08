# Backlog

<!-- Work not yet started. Rules are in dotclaude knowledge/planning.md.
Ranked is in the user's order and its top entry is next. New ideas go
under Unranked, where order means nothing. An entry leaves this file
when its issue file is created. -->

## Ranked

### ruff-migration

Replace flake8 with Ruff for linting and adopt `ruff format`. Most of
flake8's indentation, whitespace and blank-line checks (E1, E2, E3) are
preview-only in Ruff, which expects its formatter to make them
unnecessary. Settle the import-sorting approach, and update the local
pre-commit hook once Ruff runs in CI. If Ruff proves a drop-in
replacement, the user updates dotclaude's `python.md` to match.

Changes: [CI](../wiki/practices/ci.md), [testing](../wiki/practices/testing.md), [releasing](../wiki/operations/releasing.md)

- Ruff covers at least everything flake8 checks today.
- `ruff format` is adopted, in this issue rather than a later one.

### dotclaude-backlog-move

Move the entries about dotclaude's own process out of this backlog:
`specifications-knowledge-mapping`, `documentation-review-knowledge`,
`fill-rule-code-spans`, `regression-only-acceptance-tests`,
`unexercised-reference-text` and `pm-deliverable-edits`. Each belongs
in dotclaude's tracker, or is already filed there.

Changes: this backlog

### contribution-guide

Write `CONTRIBUTING.md` for outside contributors, as promised in the
PR #44 review. Open first: which tracker contributors use, since GitHub
cannot link a pull request to a file in `.context/tracker/`, and where
the minor-fix exemption ends.

Changes: [contributing](../wiki/practices/contributing.md), [README](../../README.md)

### schema-finding-taxonomy

Rework the markdown schema validator's findings so a section is
identified by name and heading level together, and give findings about
absent sections a useful position instead of line 1. Where
`missing_section` should point is still open.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

- A section's identity is its name and level together: `wrong_level`
  goes, and its cases become `missing_section` plus
  `unexpected_section`.

### free-form-subsections

Assess how usable the markdown schema is for documents with free-form
subsections. The TRR schema as written fails about half of the real
reports, because free-form `####` sections sit beside a required named
one, a `pattern: ".+"` sibling of a named entry is refused as
ambiguous, and the only working schema needs a negative lookahead.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

## Unranked

### acceptance-test-commit-hook

Acceptance Test Design commits tests that must fail, but the local
pre-commit hook runs pytest, so every such commit needs `--no-verify`,
which also skips the branch-name and commit-message checks. Settle a
convention, such as the hook skipping known acceptance-test paths
until implementation. Raised by the qa-engineer on `pypi-release`.

Changes: [testing](../wiki/practices/testing.md)

### add-docstrings

Finish docstrings on the public API and settle their format. Most
linter code and the autolink classes have plain-prose docstrings; most
element classes, the schema types, the validators' `validate()`,
`core_types` and nearly every module docstring are missing.

Changes: [repository layout](../wiki/repository/layout.md)

### ambiguity-coverage

Detect ambiguous schema matches everywhere: today sections under an
unexpected section, and duplicates in unordered mode, are never checked
for ambiguity.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

### anchor-and-fragment-checks

Make anchor and fragment checks match GitHub: anchors compare case-
sensitively, `#section` passes in a document with no headings, and a
`#fragment` or `?query` on a relative path makes the check fail.

Changes: [linter engine](../wiki/components/linter-engine.md)

### block-pattern-line-bugs

Stop block patterns crossing lines: a line holding only `#` becomes a
heading titled with the next non-blank line, a line holding only `>`
pulls the next paragraph into the quote, and a closing code fence
accepts trailing text.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

### check-url-valid-raises

Make `check_url_valid()` return every failure instead of raising: a
timeout of 0 or less, a malformed `valid_status_codes` entry from a
Python caller, and non-requests exceptions all raise today.

Changes: [linter engine](../wiki/components/linter-engine.md)

### cli-empty-flag-value

Reject an empty flag value: `--rules ""` silently skips the rules check,
or alone gives a usage error saying the flag must be provided.

Changes: [CLI](../wiki/components/cli.md)

### cli-uncaught-errors

Report every runtime error as an `error:` line: a non-UTF-8 or
unreadable input document, and a directory or unreadable configuration
file, end the run with a traceback, and a directory given as a path is
reported as missing.

Changes: [CLI](../wiki/components/cli.md)

### configuration-strategy

Decide whether the markdown schema, frontmatter schema and rules stay
three files or become one, and whether tiredize should discover a
configuration file such as `.tiredize.yaml`.

Changes: [CLI](../wiki/components/cli.md)

### container-element-model

Parse the content of container elements (block quotes, table cells,
list items) into child elements with document-root positions. Lists
are not parsed at all yet.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

### context-validation-ci

Validate `.context/` in CI with tiredize itself, against dotclaude's
canonical schemas for wiki pages, the backlog, tracker issues and
relative links, replacing the removed `validate-issues` job and the
hand-synced schema copies it used.

Changes: [CI](../wiki/practices/ci.md)

### disallow-duplicate-names

Stop a name listed twice in `elements.disallow` from doubling its
findings.

Changes: [elements rule](../wiki/components/rule-elements.md)

### element-field-types

Tidy the element types' public fields: `InlineLink` has no link text
while `InlineImage` has, and `InlineLink.title`,
`ReferenceDefinition.title` and `FrontMatter.content` can hold values
their annotations exclude.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

### empty-rules-file

Decide what an empty `--rules` file means: today it enables no rule and
exits clean, a silent no-op of the kind configuration validation
otherwise forbids.

Changes: [CLI](../wiki/components/cli.md), [linter engine](../wiki/components/linter-engine.md)

### error-discards-findings

Keep findings already produced when a later check or rule raises a
runtime error on the same path; today they are thrown away.

Changes: [CLI](../wiki/components/cli.md), [linter engine](../wiki/components/linter-engine.md)

### frontmatter-duplicate-key-checks

Compare duplicate frontmatter and schema keys as YAML keys, not Python
values (`1` and `true` are reported as duplicates), and fix the schema
error prefix that names frontmatter and calls an unhashable key a
duplicate.

Changes: [frontmatter schema validator](../wiki/components/frontmatter-schema-validator.md)

### frontmatter-heading-offset

Fix the parser dropping the first character after frontmatter: a
heading on the line right after the closing `---` loses its `#`, and
every position in such a document is one off.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

- The code is wrong, not the documentation.

### gfm-parity

Bring the remaining elements to GFM parity one element at a time, using
the skipped `gfm-parity:` tests as the register. Includes CRLF line
endings and balanced parentheses in link URLs. The remaining non-GFM
element names (`code_inline`, `quoteblock`, `header`,
`reference_definition`) wait for the planned GFM compliance audit.

Changes: [markdown parser](../wiki/components/markdown-parser.md), [testing](../wiki/practices/testing.md)

### images-not-link-checked

Decide whether the `links` rule checks image targets; inline images are
never checked today.

Changes: [links rule](../wiki/components/rule-links.md)

### invalid-frontmatter-yaml

Report frontmatter whose YAML does not parse, instead of silently
treating the document as having no frontmatter and reporting every
required field missing.

Changes: [markdown parser](../wiki/components/markdown-parser.md), [frontmatter schema validator](../wiki/components/frontmatter-schema-validator.md)

- It should fail loudly.

### line-ending-handling

Handle line endings consistently: CR-only files make `line_length` count
the `\r` and `trailing_whitespace` report every line, and CRLF is
normalised when a file is read but not for `load(text=...)`.

Changes: [markdown parser](../wiki/components/markdown-parser.md), [line_length rule](../wiki/components/rule-line-length.md), [trailing_whitespace rule](../wiki/components/rule-trailing-whitespace.md)

### link-reference-overmatch

Stop `LinkReference` matching any bracketed text, such as task-list
boxes and footnote markers, which then count as `link_reference`
elements.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

### links-config-checks

Check `links` configuration fully: `valid_status_codes: []` is accepted
and fails every link, header values are not validated, and with
`validate: false` malformed entries go unreported.

Changes: [links rule](../wiki/components/rule-links.md)

### links-exclude-malformed-url-crash

Stop a malformed URL such as `http://[::1` from aborting the whole run
when the `links` rule has `exclude` set. A skipped test in
`tests/linter/rules/test_links.py` already pins one answer: hand the
URL to `check_url_valid()` and report it.

Changes: [links rule](../wiki/components/rule-links.md)

### links-rule-cleanup

Tidy `links.py`: fold its four per-kind loops into one, and rename
`_has_checkable_scheme`, which returns true when there is no scheme.

Changes: [links rule](../wiki/components/rule-links.md)

### links-timeout

Give `links.timeout` a default, so an unresponsive host cannot stall a
run, and reject 0 or a negative value, which passes configuration checks
and then stops the run.

Changes: [links rule](../wiki/components/rule-links.md)

### load-empty-text

Let `Document.load(text="")` load an empty document, as an empty file
does, instead of raising `ValueError`.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

### markdown-schema-duplicate-keys

Reject duplicate keys in a markdown schema file, as the frontmatter
schema does; today the last one silently wins.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

### negative-maximum-length

Reject a negative or zero `line_length.maximum_length`; a negative value
reports every line at negative offsets.

Changes: [line_length rule](../wiki/components/rule-line-length.md)

### null-rule-config-message

Name the missing required key when a rule block is empty
(`line_length:` with nothing under it), the likeliest way a required
key is omitted.

Changes: [linter engine](../wiki/components/linter-engine.md)

### parser-sanitization-audit

Audit every extractor for regex backtracking and sanitize-chain gaps,
with timing thresholds. `ExtendedAutolink` is already known to be
quadratic on long whitespace-free runs.

Changes: [markdown parser](../wiki/components/markdown-parser.md), [autolinks](../wiki/components/autolinks.md)

### preamble-sections

Make text before the first heading part of the document's sections, so
links and elements there are extracted and checked.

Changes: [markdown parser](../wiki/components/markdown-parser.md)

- The code is wrong, not the documentation.

### pypi-org-transfer

Transfer the `tiredize` project on pypi.org and test.pypi.org from the
personal `daemorgue` account to the `tired-labs` organization once PyPI
approves the organization requests on each.

Changes: [releasing](../wiki/operations/releasing.md)

### python-310-ci

Test the declared minimum, Python 3.10, in CI; no workflow runs it.

Changes: [CI](../wiki/practices/ci.md), [installing and running](../wiki/operations/installing-and-running.md)

### relative-url-prefix-handling

Resolve relative link targets without a leading `.` (`sibling.md`) as
local files instead of HTTP requests. Once done, dotclaude's rule that
wiki links start with `./` can be dropped.

Changes: [linter engine](../wiki/components/linter-engine.md), [links rule](../wiki/components/rule-links.md)

### repeat-min-null

Reject `repeat: {min: null}`, which silently makes the entry non-
repeating and ignores `max`.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

### repeat-required-false

Make `required: false` on a repeating schema entry mean it may be
absent, as `repeat: {min: 0}` does now.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

- `required: false` should mean a minimum of 0.

### rule-allowed-true-noop

Decide whether `allowed: true` on `tabs` and `trailing_whitespace`, and
on `unicode` with no `exclude`, should be allowed: each leaves an
enabled rule checking nothing.

Changes: [tabs rule](../wiki/components/rule-tabs.md), [trailing_whitespace rule](../wiki/components/rule-trailing-whitespace.md), [unicode rule](../wiki/components/rule-unicode.md)

### rule-convention-enforcement

Enforce the rule module convention at discovery: a custom rule that
skips `validate_config()` loads fine, and `test_loader.py` demands at
least one key although a keyless rule is allowed.

Changes: [linter engine](../wiki/components/linter-engine.md)

### schema-child-elements

Let a schema require content inside a section, such as a table or a
list. Checking values inside that content stays out of scope.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md), [scope](../wiki/overview/scope.md)

### schema-empty-name

Reject `name: ""` in a markdown schema, which is accepted and renders as
`'None'` in messages.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

### schema-nonstring-key-crash

Report an unknown schema key that YAML reads as a non-string (`1: x`) as
a schema error; both schema loaders raise `TypeError` today, which the
CLI does not catch.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md), [frontmatter schema validator](../wiki/components/frontmatter-schema-validator.md)

### schema-out-of-order-findings

Make out-of-order findings consistent: a non-repeating section reported
`out_of_order` is never level-checked, and a skipped optional entry
whose section appears later reports `unexpected_section` instead of
`out_of_order`.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

### stale-context-references

Update code and test comments that point at removed `.context/issues/`
and `.context/specifications/` files, so they point at the wiki or say
what they mean without a reference.

Changes: [testing](../wiki/practices/testing.md)

### test-suite-audit

Review the whole test suite (1,128 tests) for tests that only check a
one-time change, such as a file deleted, a value set or a structure
built, rather than behavior that can regress, and remove them. Found on
`pypi-release`, where 29 of 40 acceptance tests were of this kind.

Changes: [testing](../wiki/practices/testing.md)

### test-file-layout

Rename the test files that break dotclaude's one-test-file-per-module
rule, or record an override.

Changes: [repository layout](../wiki/repository/layout.md)

### unicode-bom

Stop the `unicode` rule reporting a UTF-8 byte-order mark.

Changes: [unicode rule](../wiki/components/rule-unicode.md)

### user-doc-wording

Correct the README's "regex-based parser" claim and the history wording
("no longer", "now") in its `links` section, and the stale header
comment in `tests/markdown/types/test_link_gfm_autolinks.py`.

Changes: [README](../../README.md)

### venv-path-for-tests

The local test command (`.venv/bin/pytest`, and the pre-commit hook's
`.venv/bin/python -m pytest`) does not put `.venv/bin` on PATH, so a
test that finds the `tiredize` console script with `shutil.which` can
pick up an unrelated install elsewhere on PATH. Run tests in an
activated venv, or have such tests look beside `sys.executable`.
Raised by the software-engineer on `pypi-release`.

Changes: [testing](../wiki/practices/testing.md)

### specifications-knowledge-mapping

`AGENTS.md` maps a `specifications` knowledge file to the
technical-reference and architecture-review steps, but dotclaude has no
`knowledge/specifications.md`. Create it or drop the mapping. Raised by
the technical-architect on `pypi-release`.

Changes: `AGENTS.md`

### readme-style-pass

The README predates the markdown-style rules: most prose paragraphs
wrap near 72 columns instead of filling to 79, and it uses em dashes
and `--` separators. Bring the whole file into line in one pass.
Raised by the proofreader on `pypi-release`.

Changes: [README](../../README.md)

### documentation-review-knowledge

The documentation-review step names markdown-style and
ai-prose-hygiene as its mapped knowledge, but tiredize's `AGENTS.md`
maps nothing to `user-documentation` or `documentation-review`, so the
lens comes only from the step file's Inputs line. Add the mapping or
make the step file state its default knowledge. Raised by the
proofreader on `pypi-release`.

Changes: `AGENTS.md`

### fill-rule-code-spans

dotclaude's markdown-style "fill to 79" rule does not say whether a
line may break early to keep an inline code span whole. Settle it in
the knowledge file. Raised by the proofreader on `pypi-release`.

Changes: dotclaude `knowledge/markdown-style.md`

### regression-only-acceptance-tests

Put the rule settled on `pypi-release` into dotclaude's
acceptance-test-design guidance: committed acceptance tests cover only
behavior that can regress, and one-time criteria get evidence at
Acceptance Verification. On `pypi-release`, 30 of 40 first-draft tests
were thrown away. Raised by the workflow-owner.

Changes: dotclaude `knowledge/testing.md` or the step 2 file

### unexercised-reference-text

When a technical reference describes operational behavior nobody has
run, such as re-runs and approval expiry, step 6 should mark it as
unexercised and keep it minimal. Speculative recovery text drove most
of `pypi-release`'s three architecture-review iterations. Raised by
the workflow-owner.

Changes: dotclaude step 6 file

### pm-deliverable-edits

Say whether the PM may edit a deliverable directly, as it did to a
wiki sentence on `pypi-release` (0e11632), or must route the edit to
the producing step; if it may, the next review gate should check the
edit by name. Raised by the workflow-owner.

Changes: dotclaude PM function or workflow overview

### tooling-test-command-scan

In `tests/test_tooling.py`, `_tools_invoked` reads only the first six
words of a command, so a tool named after a long option list, such as
`uv run ... --group coverage coveralls`, is not seen as run. Widen the
scan so the tests do not depend on how a command is written. Raised by
the software-engineer on `tooling-migration`.

### codecov-evaluation

Evaluate Codecov against Coveralls for failing a pull request on a
coverage regression. Codecov keeps its rules in a versioned
`codecov.yml` and can check patch coverage (the lines a PR adds);
Coveralls keeps its drop threshold in its web settings.

Changes: [CI](../wiki/practices/ci.md)

- The deciding value is failing on coverage regression at a threshold.
- The uploader must be lockable and hash-checked like every other CI
  package; check what `codecov-cli`'s `sentry-sdk` sends back.
- Codecov's free plan covers public repos without upload limits. Its
  SAML is inherited from GitHub sign-in, which needs GitHub
  Enterprise Cloud; the org is on Team, so SAML is not a factor.

### doc-decision-wiki-sweep

Have the architecture review's documentation decision also search the
wiki for facts the change made stale, not only name the user-facing
surface. On `tooling-migration` the ghostwriter found the same stale
`pip install -e .` guidance in two wiki pages the decision did not
list. Raised by the ghostwriter; for the workflow owner to review in
dotclaude's `07-architecture-review.md`.

Changes: dotclaude `workflows/software-engineering/07-architecture-review.md`
