# Project Context

Project-specific context for the tiredize repository.

## Project Overview

Tiredize is a schema-driven markdown validation and linting tool. It parses
markdown documents into a structured representation and runs configurable lint
rules against them. The project is in active early development.

The tool was created to enforce quality control on Technique Research Reports
(TRRs) published by TIRED Labs, a cybersecurity research collective focused on
adversary behavior analysis, emulation, and detection. TRRs follow a rigid
document structure (specific sections in a specific order, required frontmatter
fields, consistent formatting) and no existing markdown linter supported
enforcing that kind of structural schema.

While the primary use case is TIRED Labs documentation, tiredize is designed to
be general-purpose. The document structure is defined via external configuration
files so that any project with structured markdown documentation can use it.
The tool is open-source and intended for broad adoption.

## Design Intent

The CLI accepts up to three configuration inputs, each targeting a different
validation concern. The final configuration format is still being designed.

### Markdown Schema (`--markdown-schema`)

Defines the expected section structure of a document: which sections must be
present, their required order, whether sections are optional or repeating, and
section name matching (exact or regex). Intended validations include:

- Missing required section raises an error
- Unexpected section raises an error
- Section appearing more times than allowed raises an error
- Section appearing fewer times than required raises an error

This is not yet implemented (the handler in `cli.py` is a stub).

### Frontmatter Schema (`--frontmatter-schema`)

Defines required frontmatter fields, accepted types, and accepted values. The
goal is to make TRRs programmatically parsable for presentation via web
frontends (e.g., Hugo) where metadata like tactics, techniques, procedures,
and ID numbers are used for search, indexing, and display.

This is not yet implemented (the handler in `cli.py` is a stub).

### Linter Rules (`--rules`)

A pluggable rule engine for style and formatting checks: line length, whitespace
usage, link validation, list style (dash vs plus vs asterisk), table formatting,
link style (reference vs inline), and more. Users can add custom rules by
following the module naming convention. This subsystem is functional and is the
most developed part of the tool.

### Configuration File Strategy

There is an open question about whether to consolidate all three configs into a
single file or keep them separate. Separate files have the advantage that style
rules can be shared across projects while schemas differ per project. This
decision has not been finalized.

## Entry Point

- `tiredize.cli:main`

## Dependencies

Production dependencies are declared in `pyproject.toml`:

- `PyYAML` — YAML parsing (frontmatter, config files)
- `requests` — HTTP requests (link validation)

Development dependencies are installed manually (not declared in pyproject):

- `pytest` — test runner
- `pytest-cov` — coverage reporting
- `flake8` — linter

## Project Structure

```
tiredize/                  # Main package
├── core_types.py          # Shared dataclasses: Position, RuleResult
├── cli.py                 # CLI entry point (argparse)
├── linter/                # Linting engine
│   ├── engine.py          # Rule discovery, selection, and execution
│   ├── rules/             # Auto-discovered rule modules
│   │   ├── line_length.py
│   │   ├── links.py
│   │   ├── tabs.py
│   │   └── trailing_whitespace.py
│   └── utils.py           # Config helpers, URL validation
└── markdown/              # Markdown parser
    ├── types/             # Dataclass-based element types
    │   ├── code.py        # CodeBlock, CodeInline
    │   ├── document.py    # Document (top-level container)
    │   ├── frontmatter.py # FrontMatter
    │   ├── header.py      # Header
    │   ├── image.py       # InlineImage
    │   ├── link.py        # InlineLink, BracketLink, BareLink
    │   ├── list.py        # List
    │   ├── quoteblock.py  # QuoteBlock
    │   ├── reference.py   # LinkReference, ImageReference, ReferenceDefinition
    │   ├── section.py     # Section
    │   └── table.py       # Table
    └── utils.py           # Regex helpers: search_all_re, sanitize_text

tests/                     # Mirrors source structure
├── linter/rules/          # Engine and rule loader tests
├── markdown/types/        # Per-type parser tests
└── test_cases/            # Fixture data (markdown files, example rules)
```

## Code Conventions

### Docstrings

Do not add docstrings to existing code. The project API is still stabilizing
and documenting moving targets creates maintenance burden. Docstrings will be
added when the interfaces are stable and the markdown module is ready for
external consumers.

### Regex Constants

Regex patterns are class-level constants prefixed with `RE_` (e.g.,
`RE_HEADER`, `RE_CODEBLOCK`) and use `re.VERBOSE` syntax.

### Position Tracking

All parsed elements carry a `Position(offset, length)` where `offset` is
relative to the document root (byte 0 of the original file content). The
`base_offset` parameter threads this through nested extraction calls.

### Markdown Type Pattern

Each markdown element type follows this pattern:

- A frozen or mutable dataclass with a `position: Position` field
- A class-level regex constant (`RE_*`) using `re.VERBOSE` syntax
- A `@staticmethod extract(text: str, base_offset: int = 0) -> list[T]`
  method that finds all instances in the given text
- A `@staticmethod sanitize(text: str) -> str` method that replaces matched
  regions with whitespace (preserving offsets for downstream extractors)

### Sanitize Chain

Extractors call `sanitize()` on higher-precedence types before running their
own regex to avoid false matches. For example, link extraction sanitizes out
code blocks and inline code first because a URL inside a fenced code block is
not a rendered link.

The precedence order was determined empirically by testing against GitHub's
markdown rendering behavior. It is not yet exhaustive — edge cases remain and
the ordering should be validated with unit tests against GitHub-Flavored
Markdown (GFM) rendering rules.

### Linter Rule Pattern

Each rule is a Python module under `tiredize/linter/rules/`. Rules are
auto-discovered at runtime. A valid rule module must:

1. Be a non-private module (filename must not start with `_`)
2. Expose a `validate(document, config) -> list[RuleResult]` function
3. Return `RuleResult` instances with `rule_id=None` (the engine fills this in)

The rule ID is derived from the module filename (e.g., `line_length.py`
produces rule ID `line_length`).

Rule configuration values are accessed through typed helpers in
`tiredize/linter/utils.py`: `get_config_int`, `get_config_str`,
`get_config_bool`, `get_config_dict`, `get_config_list`.

## CI

GitHub Actions runs on every push (`.github/workflows/ci.yaml`):

1. Install dependencies (`pytest`, `pytest-cov`, `flake8`)
2. Install tiredize in editable mode (`pip install -e .`)
3. Lint with flake8
4. Run tests with coverage

A separate workflow handles publishing to TestPyPI on version tags.

## TODO

Tracked next steps for the project:

- [ ] Investigate replacing flake8 with Ruff as the project linter
- [x] Add missing `__init__.py` files in test subdirectories
- [ ] Write unit tests to validate the sanitize chain precedence order
      against GitHub-Flavored Markdown rendering rules
- [ ] Migrate existing code to PEP 8 import grouping (blank lines between
      stdlib, third-party, and local groups with section comments)
- [ ] Design and implement the markdown schema configuration format
- [ ] Design and implement the frontmatter schema configuration format
- [ ] Finalize the configuration file strategy (single file vs separate)
- [ ] Fix Document._parse slug update to propagate
      dataclasses.replace() through subsection references. Currently
      subsections point to stale pre-replace objects.
