# Backlog

<!-- Work not yet started. Rules are in dotclaude knowledge/planning.md.
Ranked is in the user's order and its top entry is next. New ideas go
under Unranked, where order means nothing. An entry leaves this file
when its issue file is created. -->

## Ranked

### pypi-release

Publish tiredize to the production PyPI, which users have asked for;
releases go only to TestPyPI today, so `pip install tiredize` in the
README does not work. Scoping must settle how the publish job
authenticates, which overlaps `ci-secrets-in-aws`.

Changes: [releasing](../wiki/operations/releasing.md), [installing and running](../wiki/operations/installing-and-running.md), [README](../../README.md)

### ci-secrets-in-aws

Keep no long-lived secret for this repo in GitHub: the credentials
tiredize's workflows use should live in AWS, not in GitHub Actions
secrets.

Changes: [releasing](../wiki/operations/releasing.md), [CI](../wiki/practices/ci.md)

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

### add-docstrings

Finish docstrings on the public API and settle their format. Most
linter code and the autolink classes have plain-prose docstrings; most
element classes, the schema types, the validators' `validate()`,
`core_types` and nearly every module docstring are missing.

Changes: [repository layout](../wiki/repository/layout.md)

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

### invalid-frontmatter-yaml

Report frontmatter whose YAML does not parse, instead of silently
treating the document as having no frontmatter and reporting every
required field missing.

Changes: [markdown parser](../wiki/components/markdown-parser.md), [frontmatter schema validator](../wiki/components/frontmatter-schema-validator.md)

- It should fail loudly.

### links-exclude-malformed-url-crash

Stop a malformed URL such as `http://[::1` from aborting the whole run
when the `links` rule has `exclude` set. A skipped test in
`tests/linter/rules/test_links.py` already pins one answer: hand the
URL to `check_url_valid()` and report it.

Changes: [linter rules](../wiki/components/linter-rules.md)

### links-rule-cleanup

Tidy `links.py`: fold its four per-kind loops into one, and rename
`_has_checkable_scheme`, which returns true when there is no scheme.

Changes: [linter rules](../wiki/components/linter-rules.md)

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

### relative-url-prefix-handling

Resolve relative link targets without a leading `.` (`sibling.md`) as
local files instead of HTTP requests. Once done, dotclaude's rule that
wiki links start with `./` can be dropped.

Changes: [linter engine](../wiki/components/linter-engine.md), [linter rules](../wiki/components/linter-rules.md)

### repeat-required-false

Make `required: false` on a repeating schema entry mean it may be
absent, as `repeat: {min: 0}` does now.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md)

- `required: false` should mean a minimum of 0.

### schema-child-elements

Let a schema require content inside a section, such as a table or a
list. Checking values inside that content stays out of scope.

Changes: [markdown schema validator](../wiki/components/markdown-schema-validator.md), [scope](../wiki/overview/scope.md)

### stale-context-references

Update code and test comments that point at removed `.context/issues/`
and `.context/specifications/` files, so they point at the wiki or say
what they mean without a reference.

Changes: [testing](../wiki/practices/testing.md)

### tooling-migration

Evaluate Ruff in place of flake8, declare development dependencies in
`pyproject.toml` (`.[dev]`), and finish the import-grouping comments in
the seven test files that lack them.

Changes: [CI](../wiki/practices/ci.md), [testing](../wiki/practices/testing.md)

### user-doc-wording

Correct the README's "regex-based parser" claim and the history wording
("no longer", "now") in its `links` section, and the stale header
comment in `tests/markdown/types/test_link_gfm_autolinks.py`.

Changes: [README](../../README.md)
