# Specification: CLI

## Overview

The CLI is the process-level entry point to tiredize. It parses
arguments, loads each requested document, dispatches to the linter and
the two schema validators, prints their output, and returns the process
exit status. Located in `tiredize/cli.py`, with `tiredize/__main__.py`
providing module execution.

The CLI owns argument parsing, orchestration order, output streams, and
the exit-status contract. It owns no validation logic of its own: rule
execution belongs to the linter (`specifications/linter.md`), document
parsing to the markdown parser (`specifications/markdown-parser.md`),
and structural and frontmatter checks to the two validators
(`specifications/markdown-schema-validator.md`,
`specifications/frontmatter-schema-validator.md`). The CLI translates
what those subsystems raise or return into a status code and a stream.

**This document is partial.** It specifies the exit-status contract and
the stream and abort semantics that go with it — nothing more. The
command-line flags, the finding output format beyond the shape named
below, and the way configuration files are located and resolved are
real behavior that this document does not yet describe. Silence here
is an unwritten section, not an absence of behavior; read
`tiredize/cli.py` for anything this document does not cover.

## Contracts and Interfaces

### Entry Points

Two entry points exist and both dispatch to `tiredize.cli:main`:

```
tiredize [OPTIONS] [PATHS...]              # console script
python -m tiredize [OPTIONS] [PATHS...]    # module execution
```

They take the same argument surface and are required to produce the
same stdout, the same stderr, and the same exit status for any given
argument list.

The console script is generated from `[project.scripts]` in
`pyproject.toml` and wraps the call in `sys.exit(...)`. Module
execution has no such wrapper, so `tiredize/__main__.py` raises the
status itself:

```python
# tiredize/__main__.py
raise SystemExit(main())
```

### main

```python
# tiredize/cli.py
def main(argv: list[str] | None = None) -> int:
```

Validates every requested path and returns the process exit status.
`argv` defaults to `sys.argv[1:]` via argparse. The return value is the
contract; `main()` does not call `sys.exit()` itself, and a caller that
discards the return value discards the entire failure signal.

Argparse's own errors — an unknown flag, a flag missing its value,
`--help` — are the one exception: argparse raises `SystemExit` from
inside `main()` rather than letting it return.

## File Layout

| File                        | Purpose                             |
|-----------------------------|-------------------------------------|
| `tiredize/cli.py`           | Argument parsing, orchestration, `main` |
| `tiredize/__main__.py`      | `python -m tiredize` entry point    |
| `tests/test_cli.py`         | In-process tests of `main`          |
| `tests/test_main_module.py` | Process-level tests of `-m`         |

## Exit Status Contract

Every invocation exits with one of exactly three statuses.

| Status | Meaning                                                |
|--------|--------------------------------------------------------|
| `0`    | Every path was loaded and produced no findings         |
| `1`    | At least one path produced findings, or a runtime error occurred |
| `2`    | Usage error                                            |

A usage error is either no positional paths, or none of the three
configuration flags (`--rules`, `--markdown-schema`,
`--frontmatter-schema`). It prints the usage message and an
explanatory line to stderr. Argparse's own errors also exit `2`, by
raising `SystemExit(2)` from within `main()`.

### Findings and Runtime Errors

Status `1` covers two categories that differ in how they affect the
rest of the run.

**Findings** are what a check reports about a document: a linter rule
violation, a markdown schema mismatch, or a frontmatter schema
violation.

**Runtime errors** are what prevents a check from running at all: an
input document that does not exist, a configuration file that is
missing or unparseable, an unknown rule id, an invalid rule
configuration, or an ambiguous markdown schema. The subsystems signal
these by raising — `FileNotFoundError`, `ValueError`, `yaml.YAMLError`,
`RuleNotFoundError`, `AmbiguityError` — and the CLI catches them at the
call site.

### Processing Semantics

**Errors abort; findings continue.** Findings do not stop the run:
every path is processed, every finding is reported, and the status is
`1` at the end. A runtime error does stop the run: the first one prints
to stderr and `main()` returns `1` immediately, leaving every remaining
path unprocessed.

This holds for a missing input document exactly as it does for a bad
configuration file — a path that cannot be loaded aborts the run rather
than being skipped. It follows that a run's output is not a complete
report unless it ended in status `0` or `1`-from-findings; a `1` from a
runtime error means the remaining paths were never looked at.

Per-path processing order is: load the document, then run rules,
markdown schema, and frontmatter schema in that order, for whichever
flags were given. Findings from all three accumulate before any are
printed, so a single path's findings are printed together.

### Output Streams

| Stream | Content                                                  |
|--------|----------------------------------------------------------|
| stdout | Findings, as `path:line:col: [rule_id] message`           |
| stdout | The per-file `path: no issues found.` line               |
| stderr | Runtime errors, as `error: <message>`                    |
| stderr | The usage message and the usage-error explanation        |

Findings never go to stderr and runtime errors never go to stdout.
Line and column come from `Document.line_col()`, which resolves a
character offset into the document string: the line is 1-based, the
column 0-based, and multi-byte and astral-plane characters each count
as one column.

## Design Decisions

- **Errors abort, findings continue.** One rule rather than two axes.
  The alternative considered was "per-document problems continue,
  global problems abort", which lets a batch run report on the
  survivors of a missing file. That was rejected because it makes the
  exit-status contract unpredictable unless the reader knows which
  category a given error falls into. The chosen rule costs the batch
  behavior and buys a contract that can be stated in one sentence.

- **`main()` returns rather than exits.** The status is a return value
  so that `main()` is callable in-process and testable without a
  subprocess. The cost is that every entry point must propagate it;
  both do.

- **Both entry points pin `prog="tiredize"`.** The argument parser sets
  `prog` explicitly rather than letting argparse derive it from
  `sys.argv[0]`, which would render as `__main__.py` under module
  execution. Without the pin, the two entry points emit different usage
  text and the stream-parity contract does not hold.

- **Three statuses, no more.** Runtime errors share status `1` with
  findings rather than taking a status of their own. The stream a
  message arrives on distinguishes them: a caller that needs to tell
  the two apart reads stderr, not the status code.
