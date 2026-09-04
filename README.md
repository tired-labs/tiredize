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
positional arguments and configuration via flags.

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

The command prints rule violations in `file:line:col: [rule_id] message`
format and returns a nonzero exit code when validation fails, making it
suitable for pre-commit hooks and CI/CD pipelines.

## Configuration

### Markdown Schema

A YAML file defining the expected section structure. Sections can be
required or optional, matched by exact name or regex pattern, and
allowed to repeat with min/max bounds. Nested sections are supported.

Use `allow_subsections` when a section's internal structure is free-form:
`true` accepts any subsection tree beneath it without inspecting it, and
`false` forbids subsections entirely. This avoids having to declare a
catch-all `pattern` at every heading level just to permit prose that
authors organize differently. It cannot be combined with `sections` on the
same entry.

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
    # Authors structure results differently; accept whatever they write.
    allow_subsections: true
  - name: "References"
    level: 1
    # A flat list of references, no subsections.
    allow_subsections: false
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

#### line_length

Flags lines that exceed a maximum character count. Line endings and
newline characters are excluded from the count. Length is measured in
Unicode characters, not bytes.

| Option | Type | Description |
| --- | --- | --- |
| `maximum_length` | int | Maximum allowed line length in characters. |
| `exclude` | list | Element types whose lines are skipped. See [Recognized markdown element names](#recognized-markdown-element-names). Any line that overlaps with a listed element is exempt. |

```yaml
line_length:
  maximum_length: 80
  exclude:
    - table
    - link_inline
```

#### tabs

Flags tab characters anywhere in the document.

| Option | Type | Description |
| --- | --- | --- |
| `allowed` | bool | When `false`, any tab character is a violation. |

```yaml
tabs:
  allowed: false
```

#### trailing_whitespace

Flags lines that end with one or more whitespace characters before the
line ending.

| Option | Type | Description |
| --- | --- | --- |
| `allowed` | bool | When `false`, trailing whitespace on any line is a violation. |

```yaml
trailing_whitespace:
  allowed: false
```

#### unicode

Enforces whether unicode (non-ASCII) characters are permitted in the document.
Use `exclude` to carve out element types that are treated opposite to the
`allowed` setting — for example, to forbid unicode everywhere *except* inside
code blocks.

| Option | Type | Description |
| --- | --- | --- |
| `allowed` | bool | When `true`, unicode is permitted throughout the document. When `false`, unicode is forbidden. Omitting this option disables the rule. |
| `exclude` | list | Element types that are treated opposite to `allowed`. See [Recognized markdown element names](#recognized-markdown-element-names). |

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

| Option | Type | Description |
| --- | --- | --- |
| `validate` | bool | Enable link validation. When `false`, no links are checked. |
| `timeout` | int | Timeout in seconds for HTTP requests. |
| `headers` | dict | HTTP headers to include in every request (e.g. `Authorization`). |
| `valid_status_codes` | list | HTTP status codes treated as valid. Defaults to all 2xx and 3xx codes. Entries may be exact integers (`200`) or class wildcards (`2xx`, `3xx`). |
| `exclude` | list | Domain patterns to skip. Supports `*` as a wildcard (e.g. `*.mycompany.com`). Relative paths and anchors are unaffected. |

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

| Option | Type | Description |
| --- | --- | --- |
| `disallow` | list | Element types that must not appear. See [Recognized markdown element names](#recognized-markdown-element-names). |

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

1. Create a Python module (e.g., `my_rule.py`) with a `validate`
   function:

   ```python
   from tiredize.core_types import Position, RuleResult
   from tiredize.markdown.types.document import Document

   def validate(
       document: Document,
       config: dict,
   ) -> list[RuleResult]:
       results = []
       # Your validation logic here.
       # Return RuleResult instances with rule_id=None
       # (the engine fills it in from the module name).
       return results
   ```

2. Place the module in the built-in rules package
   (`tiredize/linter/rules/`). This requires an editable install
   (`pip install -e .`) or a project fork. The module must be
   non-private (no leading underscore) and expose a `validate`
   function.

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
