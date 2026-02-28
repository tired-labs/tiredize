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
resolution, and relative file path verification). Users can add custom
rules by dropping a Python module into a rules package.

**Markdown parser** -- A regex-based parser that extracts headers,
sections, code blocks (fenced and inline), links (inline,
reference-style, bracket, and bare), images, tables, block quotes,
lists, and frontmatter into typed dataclass elements with accurate
position tracking.

**Frontmatter schema validation** -- Planned. The CLI flag exists but
the handler is a stub.

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

### Combine both

```bash
tiredize --markdown-schema schema.yaml --rules rules.yaml document.md
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

See the [schema validator specification][spec-validator] for the full
format reference, including all properties, constraints, and validation
algorithm details.

### Linter Rules

A YAML file where each top-level key is a rule ID and its value is the
rule's configuration. Only rules with an entry in the config file are
enabled.

```yaml
line_length:
  maximum_length: 80

tabs:
  allowed: false

trailing_whitespace:
  allowed: false

links:
  validate: true
  timeout: 5
```

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

2. Place the module in a package alongside the built-in rules, or in
   your own package that follows the same convention (non-private
   modules exposing a `validate` function).

The rule ID is derived from the module filename (e.g., `my_rule.py`
produces rule ID `my_rule`). Configuration values for your rule are
passed via the `config` dict from the YAML file.

See the [linter specification][spec-linter] for the full rule pattern
and available configuration helpers.

## License

[GPL-3.0](LICENSE)

[TIRED Labs]: https://www.tired-labs.org/
[TRR]: https://github.com/tired-labs/techniques
[spec-validator]: .context/specifications/markdown-schema-validator.md
[spec-linter]: .context/specifications/linter.md
