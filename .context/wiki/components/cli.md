# Command-Line Interface

## Overview

The CLI is the process-level entry point to tiredize. It parses
arguments, loads each requested document, hands it to the linter and
the two schema validators, prints their findings, and returns the exit
status. It lives in `tiredize/cli.py`, with `tiredize/__main__.py`
providing module execution.

The CLI owns argument parsing, the order checks run in, the output
streams and the exit-status contract. It owns no validation logic:
parsing belongs to the [markdown parser](./markdown-parser.md), rule
execution to the [linter engine](./linter-engine.md), and structural
and frontmatter checks to the [markdown schema
validator](./markdown-schema-validator.md) and the [frontmatter schema
validator](./frontmatter-schema-validator.md). The CLI turns what they
raise or return into a status code and a stream. How the parts fit
together is in [the pipeline](../architecture/pipeline.md).

## Contracts and Interfaces

### Entry Points

Two entry points exist and both call `tiredize.cli:main`:

```
tiredize [--rules FILE] [--markdown-schema FILE] [--frontmatter-schema FILE] PATH...
python -m tiredize [same arguments]
```

They take the same arguments and must produce the same stdout, stderr
and exit status for any argument list.

The console script is generated from `[project.scripts]` in
`pyproject.toml` and wraps the call in `sys.exit(...)`. Module execution
has no such wrapper, so `tiredize/__main__.py` raises the status itself:

```python
# tiredize/__main__.py
raise SystemExit(main())
```

### Arguments

| Argument               | Meaning                                         |
|------------------------|-------------------------------------------------|
| `--rules`              | YAML file configuring linter rules              |
| `--markdown-schema`    | YAML file describing the section structure      |
| `--frontmatter-schema` | YAML file describing the frontmatter fields     |
| `PATH...`              | Markdown files to check                         |
| `-h`, `--help`         | Print the help text to stdout and exit `0`      |

There is no `--version` and no other flag. Each configuration flag
names its file directly; there is no configuration discovery and no
default file. A flag given twice keeps its last value. At least one
configuration flag and at least one path are required. Paths are taken
as given: the shell expands globs, and a path listed twice is checked
twice.

Configuration and schema files are read as UTF-8 whatever the platform
default. Their formats are the contracts on the [linter
engine](./linter-engine.md) (rules file), [markdown schema
validator](./markdown-schema-validator.md) and [frontmatter schema
validator](./frontmatter-schema-validator.md) pages. An empty rules
file enables no rule, so the run checks nothing and reports every path
clean.

### main

```python
# tiredize/cli.py
def main(argv: list[str] | None = None) -> int:
```

Checks every requested path and returns the exit status. `argv`
defaults to `sys.argv[1:]` through argparse. `main()` does not call
`sys.exit()`; a caller that discards the return value discards the
failure signal.

Argparse is the exception: it raises `SystemExit` from inside `main()`.
Its own errors (an unknown flag, a flag missing its value) print to
stderr and raise `SystemExit(2)`. `--help` prints to stdout and raises
`SystemExit(0)`.

## File Layout

| File                        | Purpose                                      |
|-----------------------------|----------------------------------------------|
| `tiredize/cli.py`           | Argument parsing, orchestration, `main`      |
| `tiredize/__main__.py`      | `python -m tiredize` entry point             |
| `tests/test_cli.py`         | In-process tests of `main`                   |
| `tests/test_main_module.py` | Entry-point tests, subprocess and in-process |

## Exit Status

| Status | Meaning                                                          |
|--------|------------------------------------------------------------------|
| `0`    | Every path loaded and produced no findings, or `--help`          |
| `1`    | At least one path produced findings, or a runtime error occurred |
| `2`    | Usage error                                                      |

A usage error is no positional paths, or none of the three flags. It
prints the usage message and an explanatory line to stderr. Argparse's
own errors also exit `2`.

### Findings and Runtime Errors

**Findings** are what a check reports about a document: a linter rule
violation, a markdown schema mismatch, or a frontmatter schema
violation.

**Runtime errors** stop a check from running at all: an input document
that does not exist, a configuration or schema file that is missing or
unparseable, an unknown rule id, an invalid rule configuration, or an
ambiguous markdown schema. The subsystems raise `FileNotFoundError`,
`ValueError`, `yaml.YAMLError`, `RuleNotFoundError` or `AmbiguityError`,
and the CLI catches them around each check.

### Processing Order

Findings never stop the run: every path is processed, every finding is
reported, and the status is `1` at the end. A runtime error does stop
it: the first one prints to stderr and `main()` returns `1` at once,
leaving the remaining paths unprocessed. This holds for a missing input
document as for a bad configuration file. A `1` from a runtime error
therefore means the remaining paths were never looked at.

Paths are processed in the order given. For each path the CLI loads the
document, then runs the rules, the markdown schema and the frontmatter
schema, in that order, for whichever flags were given. Configuration
and schema files are read again for each path. Findings from all three
are collected before any is printed, so one path's findings print
together, in this order and not sorted by line:

1. rule findings, rule by rule in the order the rules file lists them,
   each rule's in the order it reports them;
2. markdown schema findings;
3. frontmatter schema findings.

### Output Streams

| Stream | Content                                             |
|--------|-----------------------------------------------------|
| stdout | Findings, as `path:line:col: [rule_id] message`      |
| stdout | `path: no issues found.` for a path with no findings |
| stdout | The `--help` text                                   |
| stderr | Runtime errors, as `error: <message>`               |
| stderr | The usage message and the usage-error explanation   |
| stderr | Argparse's own error messages                       |

Findings never go to stderr and runtime errors never go to stdout. Line
and column come from `Document.line_col()`: the line is 1-based, the
column 0-based, and every character, multi-byte or astral, counts as one
column.

## Design Decisions

- **Errors abort, findings continue.** One rule instead of two axes.
  "Per-document problems continue, global problems abort" would let a
  batch run report on the files that survive a missing one, but it makes
  the exit status unpredictable unless the reader knows which category
  each error falls in. The chosen rule costs that batch behaviour and
  buys a contract that fits in one sentence.
- **`main()` returns rather than exits,** so it can be called and tested
  in-process without a subprocess. The cost is that every entry point
  must pass the status on; both do.
- **`python -m tiredize` raises the status.** Module execution is what
  hooks and CI use when the console script is not on `PATH`, so it has
  to be able to fail a build. `raise SystemExit(...)` matches the idiom
  at the bottom of `cli.py`.
- **Both entry points pin `prog="tiredize"`.** Left to argparse, `prog`
  renders as `__main__.py` under module execution, and the two entry
  points would print different usage text.
- **Three statuses, no more.** Runtime errors share `1` with findings.
  The stream tells them apart: a caller that needs to know reads
  stderr.

## Open Questions

- An empty `--rules` file enables nothing and exits `0`, a silent no-op of the kind configuration validation otherwise forbids.
