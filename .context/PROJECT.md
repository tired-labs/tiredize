# Project Context

Project-specific context for the tiredize repository. This file is the
primary reference for project-level overview and architecture.
Specification files in `.context/specifications/` contain the technical
depth.

## Project Overview

**What it does:**
Tiredize is a schema-driven markdown validation and linting tool. It
parses markdown documents into a structured representation and runs
configurable lint rules against them.

**What problem it solves:**
Technique Research Reports (TRRs) published by TIRED Labs follow a
rigid document structure (specific sections in a specific order,
required frontmatter fields, consistent formatting) and no existing
markdown linter supported enforcing that kind of structural schema.

**Who it's for:**
Primary audience is TIRED Labs contributors and reviewers. Designed as
general-purpose -- the document structure is defined via external
configuration files so that any project with structured markdown
documentation can use it. Open-source and intended for broad adoption.

**Design boundaries:**
The tool validates document structure and style, not document content.
Structural checks (sections exist, correct order, correct level) belong
in the schema validator. Style and formatting checks (line length,
whitespace, link validity) belong in linter rules. Content correlation
across sections is out of scope.

## Architecture

The CLI (`tiredize/cli.py`) accepts up to three configuration inputs,
each targeting a different validation concern. It orchestrates three
subsystems:

1. **Markdown Parser** (`tiredize/markdown/`) -- Parses raw markdown
   into typed dataclass elements. Owns the document model.
   Spec: `specifications/markdown-parser.md`.

2. **Linter** (`tiredize/linter/`) -- Pluggable rule engine for style
   and formatting checks. Owns rule discovery and execution.
   Spec: `specifications/linter.md`.

3. **Markdown Schema Validator** (`tiredize/validators/`) -- Validates
   document structure against a YAML schema. Owns structural
   validation. Spec: `specifications/markdown-schema-validator.md`.

**Boundary rule:** Structural checks belong in the schema validator,
not in linter rules. Content checks belong in linter rules, not in
the schema validator.

**Frontmatter schema** (`--frontmatter-schema`) is a planned fourth
concern: validating required frontmatter fields, accepted types, and
accepted values. The handler in `cli.py` is a stub. See issue
`frontmatter-schema.md`.

**Configuration file strategy** is an open question: whether to
consolidate all configs into a single file or keep them separate.
Separate files have the advantage that style rules can be shared
across projects while schemas differ per project. See issue
`configuration-strategy.md`.

## Entry Point

- `tiredize.cli:main`

## Dependencies

Production dependencies are declared in `pyproject.toml`:

- `PyYAML` -- YAML parsing (frontmatter, config files)
- `requests` -- HTTP requests (link validation)

Development dependencies are installed manually (not declared in pyproject):

- `pytest` -- test runner
- `pytest-cov` -- coverage reporting
- `flake8` -- linter

## Project Structure

```
tiredize/                  # Main package
├── core_types.py          # Shared dataclasses: Position, RuleResult
├── cli.py                 # CLI entry point (argparse)
├── linter/                # Linting engine and rule modules
│   └── rules/             # Auto-discovered rule modules
├── markdown/              # Markdown parser
│   └── types/             # Dataclass-based element types
└── validators/            # Validation engines

tests/                     # Mirrors source structure
├── linter/rules/          # Engine and rule tests
├── markdown/types/        # Per-type parser tests
├── validators/            # Validator tests
└── test_cases/            # Fixture data
```

Individual file listings are in the relevant specification files under
`.context/specifications/`.

## CI

GitHub Actions runs on every push (`.github/workflows/ci.yaml`):

1. Install dependencies (`pytest`, `pytest-cov`, `flake8`)
2. Install tiredize in editable mode (`pip install -e .`)
3. Lint with flake8
4. Run tests with coverage

A separate workflow handles publishing to TestPyPI on version tags.
