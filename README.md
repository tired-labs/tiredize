# Tiredize

[![Run tests and upload coverage](https://github.com/tired-labs/tiredize/actions/workflows/ci.yaml/badge.svg)](https://github.com/tired-labs/tiredize/actions/workflows/ci.yaml)  [![Coverage Status](https://coveralls.io/repos/github/tired-labs/tiredize/badge.svg?branch=main)](https://coveralls.io/github/tired-labs/tiredize?branch=main)

Tiredize is a schema-driven markdown validation and linting tool. It
parses markdown documents into a structured representation and validates
them against user-defined schemas and configurable lint rules. Define
what your documents should look like, and tiredize tells you where they
don't.

The tool was built to enforce quality control on [Technique Research
Reports][TRR] published by [TIRED Labs], but it is general-purpose.
Document structure is defined via external YAML configuration files, so
any project with structured markdown documentation can use it.

## Features

**Markdown schema validation** -- Define the expected section structure
of a document: which sections must exist, their heading levels, their
ordering, whether sections are optional or repeating, and section name
matching via exact string or regex. Tiredize validates the document
against the schema and reports missing, unexpected, misordered, or
incorrectly leveled sections. Supports both ordered and unordered
validation modes.

**Linter rules** -- A pluggable rule engine for style and formatting
checks. Built-in rules cover line length, tab usage, trailing
whitespace, and link validation (including HTTP checks, anchor
resolution, and relative file path verification). Advanced users can
add custom rules by modifying the built-in rules package (for example,
via an editable install or project fork).

**Markdown parser** -- A regex-based parser that extracts headers,
sections, code blocks (fenced and inline), links (inline,
reference-style, bracket, and bare), images, tables, block quotes,
and frontmatter into typed dataclass elements with accurate position
tracking. List extraction is planned but not yet implemented.

**Frontmatter schema validation** -- Validate YAML frontmatter fields
against a user-defined schema. Declare which fields must exist, their
expected types (`string`, `int`, `float`, `bool`, `date`, `list`), and
optionally constrain their values to a set of allowed entries. Detects
duplicate YAML keys, rejects map values, and enforces string-only list
items with no duplicates.

## Installation

Requires Python 3.10 or later.

```bash
pip install tiredize
```

For development:

```bash
git clone https://github.com/tired-labs/tiredize.git
cd tiredize
pip install -e .
pip install pytest pytest-cov flake8
```

## Usage

Tiredize runs from the command line. It accepts markdown files as
positional arguments and configuration via flags. There are two
equivalent ways to invoke it:

```bash
tiredize [OPTIONS] [PATHS...]
python3 -m tiredize [OPTIONS] [PATHS...]
```

The installed console script and module execution take the same
arguments and produce the same output, on the same streams, with the
same exit status. Module execution is the safer choice in a pre-commit
hook or a CI job, where the console script may not be on `PATH`. Write
`python -m tiredize` only where `python` is known to be the Python 3
interpreter tiredize was installed into — many systems ship `python3`
and no `python` at all.

The examples below use the console script.

### Validate document structure against a schema

```bash
tiredize --markdown-schema schema.yaml document.md
```

### Run linter rules

```bash
tiredize --rules rules.yaml document.md
```

### Validate frontmatter against a schema

```bash
tiredize --frontmatter-schema frontmatter.yaml document.md
```

### Combine all three

```bash
tiredize --markdown-schema schema.yaml --frontmatter-schema frontmatter.yaml --rules rules.yaml document.md
```

### Multiple files

```bash
tiredize --markdown-schema schema.yaml docs/*.md
```

For each file, in the order the paths were given, the command prints
that file's findings to stdout as `file:line:col: [rule_id] message`,
or a single `file: no issues found.` line if the file produced none.
Runtime errors go to stderr as `error: <message>`.

### Exit status

Every invocation exits with one of exactly three statuses, which is what
makes tiredize suitable for pre-commit hooks and CI/CD pipelines. Both
invocation forms return the same status for the same arguments.

| Status | Meaning |
| --- | --- |
| `0` | Every file was read and produced no findings. `--help` also exits `0`. |
| `1` | At least one file produced findings, or a runtime error occurred. |
| `2` | Usage error: no files were given, or none of `--rules`, `--markdown-schema`, and `--frontmatter-schema` was given. An unrecognized flag, or a flag missing its value, also exits `2`. |

Status `1` covers two different things, which differ in what they do to
the rest of the run.

**Findings** are what a check reports about a document: a lint rule
violation, a markdown schema mismatch, or a frontmatter schema
violation. Findings do not stop the run — every file is processed,
every finding is printed, and the status is `1` at the end.

**Runtime errors** are what stop a check from running at all: a file
that does not exist, a configuration file that is missing or
unparseable, an unknown rule ID, an invalid rule configuration, or an
ambiguous markdown schema. A runtime error does stop the run. The first
one prints to stderr and tiredize exits `1` immediately, leaving every
remaining file unprocessed.

Errors abort and findings continue, whichever way you invoke the tool.
In the run below, if `missing.md` cannot be read, tiredize reports that
error and never looks at `guide.md`:

```bash
tiredize --rules rules.yaml intro.md missing.md guide.md
```

So the output of a run that exited `1` is a complete report only when
the `1` came from findings. A `1` arriving with an `error:` line on
stderr means the remaining files were never examined.

## Configuration

### Markdown Schema

A YAML file defining the expected section structure. Sections can be
required or optional, matched by exact name or regex pattern, and
allowed to repeat with min/max bounds. Nested sections are supported.

```yaml
# Enforce that documents have these sections in order
enforce_order: true
allow_extra_sections: false

sections:
  - name: "Introduction"
    level: 1
    sections:
      - name: "Background"
        level: 2
      - name: "Scope"
        level: 2
        required: false
  - name: "Methods"
    level: 1
    sections:
      - pattern: ".+"
        level: 2
        repeat:
          min: 1
  - name: "Results"
    level: 1
  - name: "References"
    level: 1
```

See the [markdown schema validator specification][spec-validator] for the
full format reference, including all properties, constraints, and
validation algorithm details.

### Frontmatter Schema

A YAML file defining expected frontmatter fields, their types, and
optionally their allowed values.

```yaml
fields:
  status:
    type: string
    allowed:
      - draft
      - ready
      - active
      - done

  priority:
    type: string
    allowed:
      - critical
      - high
      - medium
      - low

  created:
    type: date

  tags:
    type: list
    required: false
```

See the [frontmatter schema validator specification][spec-frontmatter] for
the full format reference, including all properties, type mapping,
constraints, and error types.

### Linter Rules

A YAML file where each top-level key is a rule ID and its value is the
rule's configuration. Only rules with an entry in the config file are
enabled.

Every rule declares the configuration keys it accepts and which of them
it requires, and its configuration is checked before the rule runs.
Three things are errors, not warnings:

- a key the rule does not accept — a typo, usually;
- an accepted key holding a value of the wrong type;
- a required key that was omitted.

Each of the three prints a message to stderr naming the rule and the
offending key, then aborts the run with exit status `1`:

```
error: Rule 'line_length': unknown configuration key 'max_length'. Accepted keys: exclude, maximum_length.
```

Omitting an *optional* key is fine — the rule falls back to its own
default. The Required column in the tables below says which keys are
which. Required means the key must be *present*, not that it must be
enabled: `links: {validate: false}` is a legitimate way to turn link
checking off.

#### line_length

Flags lines that exceed a maximum character count. Line endings and
newline characters are excluded from the count. Length is measured in
Unicode characters, not bytes.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `maximum_length` | int | Yes | Maximum allowed line length in characters. |
| `exclude` | list | No | Element types whose lines are skipped. See [Recognized markdown element names](#recognized-markdown-element-names). Any line that overlaps with a listed element is exempt. Defaults to no exemptions. |

```yaml
line_length:
  maximum_length: 80
  exclude:
    - table
    - link_inline
```

#### tabs

Flags tab characters anywhere in the document.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `allowed` | bool | No | When `false`, any tab character is a violation. Tabs are forbidden when the key is omitted. |

```yaml
tabs:
  allowed: false
```

#### trailing_whitespace

Flags lines that end with one or more whitespace characters before the
line ending.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `allowed` | bool | No | When `false`, trailing whitespace on any line is a violation. Trailing whitespace is forbidden when the key is omitted. |

```yaml
trailing_whitespace:
  allowed: false
```

#### unicode

Enforces whether unicode (non-ASCII) characters are permitted in the document.
Use `exclude` to carve out element types that are treated opposite to the
`allowed` setting — for example, to forbid unicode everywhere *except* inside
code blocks.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `allowed` | bool | Yes | When `true`, unicode is permitted throughout the document. When `false`, unicode is forbidden. The key selects the mode the rule runs in, so it must be given. |
| `exclude` | list | No | Element types that are treated opposite to `allowed`. See [Recognized markdown element names](#recognized-markdown-element-names). Defaults to no exemptions. |

```yaml
# Forbid unicode everywhere except in code blocks and inline code
unicode:
  allowed: false
  exclude:
    - code_block
    - code_inline
```

```yaml
# Permit unicode everywhere except in headers
unicode:
  allowed: true
  exclude:
    - header
```

#### links

Validates that URLs in the document are reachable. Checks inline links,
angle-bracket links, bare URLs, and reference definitions. Anchors
(`#slug`) are resolved against section headings in the document. Relative
paths are checked for file existence on disk.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `validate` | bool | Yes | Enable link validation. When `false`, no links are checked. |
| `timeout` | int | No | Timeout in seconds for HTTP requests. |
| `headers` | dict | No | HTTP headers to include in every request (e.g. `Authorization`). |
| `valid_status_codes` | list | No | HTTP status codes treated as valid. Defaults to all 2xx and 3xx codes. Entries may be exact integers (`200`) or class wildcards (`2xx`, `3xx`). |
| `exclude` | list | No | Domain patterns to skip. Supports `*` as a wildcard (e.g. `*.mycompany.com`). Relative paths and anchors are unaffected. |

```yaml
links:
  validate: true
  timeout: 5
  exclude:
    - "*.mycompany.com"
    - mycompany.atlassian.net
```

#### elements

Prohibits specific markdown element types from appearing in the document.
Each occurrence of a disallowed type is reported as a separate violation.

| Option | Type | Required | Description |
| --- | --- | --- | --- |
| `disallow` | list | Yes | Element types that must not appear. See [Recognized markdown element names](#recognized-markdown-element-names). The rule inspects nothing without it. |

```yaml
elements:
  disallow:
    - link_inline
    - link_bare
```

#### Recognized markdown element names

The following names are valid in `exclude` and `disallow` lists:

| Name | Description |
| --- | --- |
| `code_block` | Fenced code block |
| `code_inline` | Inline code |
| `header` | Section header |
| `image_inline` | Inline image |
| `image_reference` | Reference-style image |
| `link_bare` | Bare URL |
| `link_bracket` | Bracket link (`<url>`) |
| `link_inline` | Inline link |
| `link_reference` | Reference-style link |
| `quoteblock` | Block quote |
| `reference_definition` | Reference link definition |
| `table` | Pipe-delimited table |

## Custom Rules

Tiredize discovers linter rules automatically from Python modules. To
add a custom rule:

1. Create a Python module (e.g., `my_rule.py`) that declares the
   configuration keys it accepts and exposes a `validate` function:

   ```python
   from tiredize.core_types import Position, RuleResult
   from tiredize.linter.utils import validate_config
   from tiredize.markdown.types.document import Document

   # The name this rule reports configuration errors under, every
   # key it accepts mapped to its type, and the subset it requires.
   _RULE_ID = "my_rule"
   _ALLOWED_KEYS = {"maximum_count": "int"}
   _REQUIRED_KEYS = ("maximum_count",)

   def validate(
       document: Document,
       config: dict,
   ) -> list[RuleResult]:
       validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)

       results = []
       # Your validation logic here.
       # Return RuleResult instances with rule_id=None
       # (the engine fills it in from the module name).
       return results
   ```

   The `validate_config()` call is not optional, and it belongs at
   the top of `validate()`, before any key is read. It raises
   `ValueError` for the three faults described under
   [Linter Rules](#linter-rules): a key the rule does not accept, an
   accepted key holding a wrong-typed value, and an omitted required
   key. A rule that skips the call reads a mistyped key as an absent
   one and then silently checks nothing, which is the failure the
   call exists to prevent.

   `_RULE_ID` names your rule in those messages, and it is the only
   place the rule's ID is written by hand: the engine never reads it,
   and derives the ID it stamps on findings from the module filename.
   Keep the two equal. Set `_RULE_ID` to anything else and a
   configuration mistake is reported against an ID that appears
   nowhere in your rules file, while findings from the same rule
   carry the filename.

   Declare a key as required when the rule does nothing without it,
   and optional when the rule can fall back to a default and still do
   its job. Each key's type is named with one of `bool`, `dict`,
   `int`, `list`, or `str`. A rule that accepts no keys at all still
   calls `validate_config()`, passing an empty `_ALLOWED_KEYS`; that
   is what makes configuring such a rule an error rather than a
   no-op.

2. Place the module in the built-in rules package
   (`tiredize/linter/rules/`). This requires an editable install
   (`pip install -e .`) or a project fork. The module must be
   non-private (no leading underscore) and expose a `validate`
   function. Discovery checks nothing beyond that, so nothing stops a
   rule that omits `validate_config()` from loading — the convention
   is yours to keep.

The rule ID is derived from the module filename (e.g., `my_rule.py`
produces rule ID `my_rule`). Configuration values for your rule are
passed via the `config` dict from the YAML file.

See the [linter specification][spec-linter] for the full rule pattern
and available configuration helpers.

## License

[GPL-3.0](LICENSE)

[TIRED Labs]: https://www.tired-labs.org/
[TRR]: https://github.com/tired-labs/techniques
[spec-validator]: https://github.com/tired-labs/tiredize/blob/main/.context/specifications/markdown-schema-validator.md
[spec-frontmatter]: https://github.com/tired-labs/tiredize/blob/main/.context/specifications/frontmatter-schema-validator.md
[spec-linter]: https://github.com/tired-labs/tiredize/blob/main/.context/specifications/linter.md
