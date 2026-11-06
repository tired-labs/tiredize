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
tiredize --version
python -m tiredize [same arguments]
```

This synopsis is illustrative. The `--help` usage line is argparse's
own: it names the values `RULES_PATH`, `MARKDOWN_SCHEMA_PATH` and
`FRONTMATTER_SCHEMA_PATH`, and shows `[paths ...]` as optional although
at least one path is required.

Both entry points take the same arguments and produce the same stdout,
stderr and exit status for any argument list, with one exception: when
an error the CLI does not handle ends the run (see Runtime Errors by
Step), the traceback on stderr shows different call frames for each.

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
| `--version`            | Print the installed version to stdout, exit `0` |

There is no other flag. Argparse's defaults apply to the flags: each
can be written `--rules FILE` or `--rules=FILE`, each can be
abbreviated to any unique prefix (`--rul FILE`), and `--` ends option
parsing.

Each configuration flag names its file directly; there is no
configuration discovery and no default file. A flag given twice keeps
its last value. A flag given an empty value (`--rules ""`) counts as
absent: its check does not run, and if no other flag has a value the
run is a usage error.

At least one configuration flag and at least one path are required.
The paths must form one contiguous group: they may come before or after
the flags, but not on both sides of them. `a.md --rules r.yaml b.md` is
an argparse error (`unrecognized arguments: b.md`, exit `2`).

Paths are taken as given: the shell expands globs, and a path listed
twice is checked twice. Directories are not searched.

Input documents and configuration files are all read as UTF-8 whatever
the platform default. The configuration formats are the contracts on
the [linter engine](./linter-engine.md) (rules file, under Rules File),
[markdown schema validator](./markdown-schema-validator.md) and
[frontmatter schema validator](./frontmatter-schema-validator.md)
pages. The CLI loads the rules file itself: an empty or comment-only
file is an empty mapping, so it enables no rule and the run reports
every path clean; a top level that is not a mapping is a runtime error;
a rule id listed twice keeps its last configuration, in the position of
its first entry.

### Version

`--version` prints one line to stdout and exits `0`:

```
tiredize X.Y.Z
```

The version is the installed distribution's, read with
`importlib.metadata.version("tiredize")`; no source file holds it. It
is set at build or install time from git tags (see
[releasing](../operations/releasing.md)), so it is a release number
such as `0.1.0` or a dev version such as `0.1.1.dev3`. The release
workflow relies on this exact line: it compares the output with
`tiredize <version>`.

When no tiredize distribution metadata is found, as when the package
is imported from a source tree that was never installed, the line is
`tiredize unknown`, still with status `0`. The lookup runs whenever the
argument parser is built, on every invocation, so missing metadata
never affects a normal run.

Like `--help`, `--version` acts as soon as argparse reads it: the
configuration flags and paths around it are not checked or loaded, and
the usage-error rule below does not apply.

### main

```python
# tiredize/cli.py
def main(argv: list[str] | None = None) -> int:
```

Checks every requested path and returns the exit status. `argv`
defaults to `sys.argv[1:]` through argparse. `main()` does not call
`sys.exit()`; a caller that discards the return value discards the
failure signal.

Two things leave `main()` without a return value. Argparse raises
`SystemExit` from inside it: its own errors (an unknown flag, a flag
missing its value, paths on both sides of the flags) print to stderr
and raise `SystemExit(2)`, and `--help` and `--version` print to stdout
and raise `SystemExit(0)`. Any exception the CLI does not handle (see Runtime
Errors by Step) propagates out of `main()` unchanged.

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
| `0`    | Every path loaded and produced no findings, `--help`, or `--version` |
| `1`    | At least one path produced findings, or a runtime error occurred |
| `2`    | Usage error                                                      |

A usage error is no positional paths, or no configuration flag with a
non-empty value. It prints the usage message and this line to stderr:

```
error: at least one of --rules, --markdown-schema, or --frontmatter-schema must be provided, and at least one path.
```

Argparse's own errors also exit `2`, printing the usage message and a
line of the form `tiredize: error: <message>`.

### Findings and Runtime Errors

**Findings** are what a check reports about a document: a linter rule
violation, a markdown schema mismatch, or a frontmatter schema
violation.

**Runtime errors** stop a check from running at all: an input document
that is missing or unreadable, a configuration or schema file that is
missing, unreadable or invalid, an unknown rule id, an invalid rule
configuration, or an ambiguous markdown schema.

### Runtime Errors by Step

The CLI catches a fixed set of exception types around each step. A
caught exception prints `error: <message>` to stderr and `main()`
returns `1` at once. Any other exception is not caught: the run ends
with a Python traceback on stderr, no `error:` line, and status `1`
from the interpreter.

| Step                 | Caught                                                                         | Not caught (traceback)                                                                  |
|----------------------|--------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Load the document    | `FileNotFoundError`                                                            | A document that is not UTF-8 (`UnicodeDecodeError`), an unreadable one (`PermissionError`) |
| Rules                | `RuleNotFoundError`, `FileNotFoundError`, `ValueError`, `yaml.YAMLError`       | A directory (`IsADirectoryError`) or unreadable file (`PermissionError`) as the rules file |
| Markdown schema      | `ValueError`, `AmbiguityError`, `FileNotFoundError`, `yaml.YAMLError`          | A directory or unreadable file as the schema file                                       |
| Frontmatter schema   | `ValueError`, `FileNotFoundError`, `yaml.YAMLError`                            | A directory or unreadable file as the schema file                                       |

`UnicodeDecodeError` is a `ValueError`, so a configuration or schema
file that is not UTF-8 is caught and printed, while an input document
that is not UTF-8 is not. Any exception a rule raises other than
`ValueError` or `RuleNotFoundError` is also uncaught.

`<message>` is the text of the raised exception. It does not name the
flag or check that failed, and it may span several lines (PyYAML parse
errors do). The messages the CLI and the document loader produce:

| Cause                                      | stderr                                              |
|--------------------------------------------|-----------------------------------------------------|
| Path that is not a regular file            | `error: Path does not exist: <path>`                |
| Missing configuration or schema file       | `error: [Errno 2] No such file or directory: '<file>'` |
| Rules file whose top level is not a mapping | `error: Expected YAML mapping in <file>, got <type>.` |
| Configuration file that is not UTF-8       | `error: 'utf-8' codec can't decode ...`             |

A directory given as a path is therefore reported as `Path does not
exist`. The other messages belong to the component that raises them:
see the [linter engine](./linter-engine.md), [markdown schema
validator](./markdown-schema-validator.md) and [frontmatter schema
validator](./frontmatter-schema-validator.md).

### Processing Order

Findings never stop the run: every path is processed, every finding is
reported, and the status is `1` at the end. A runtime error does stop
it, caught or not: `main()` ends at the first one, leaving the remaining
paths unprocessed. This holds for a missing input document as for a bad
configuration file. A `1` from a runtime error therefore means the
remaining paths were never looked at.

Paths are processed in the order given. For each path the CLI loads the
document, then runs the rules, the markdown schema and the frontmatter
schema, in that order, for whichever flags were given. Configuration
and schema files are read again for each path, so a missing or invalid
configuration file stops the run at the first path. An ambiguous
markdown schema is detected per document: earlier paths are reported
normally and the run stops at the first document with a section that
matches two schema entries.

Findings from all three checks are collected before any is printed. If
a later check on a path raises, the findings already gathered for that
path are discarded; only earlier paths' output has been printed. One
path's findings print together, in this order and not sorted by line:

1. rule findings, rule by rule in the order the rules file lists them,
   each rule's in the order it reports them;
2. markdown schema findings;
3. frontmatter schema findings.

### Output Streams

| Stream | Content                                              |
|--------|------------------------------------------------------|
| stdout | Findings, as `path:line:col: [rule_id] message`      |
| stdout | `path: no issues found.` for a path with no findings |
| stdout | The `--help` text                                    |
| stdout | The `--version` line                                 |
| stderr | Runtime errors, as `error: <message>` or a traceback |
| stderr | The usage message and the usage-error explanation    |
| stderr | Argparse's own error messages                        |

Findings never go to stderr and runtime errors never go to stdout.

`path` is the argument as normalised by `pathlib`: `./a.md` prints as
`a.md` and `docs//a.md` as `docs/a.md`; it is not made absolute or
relative. `rule_id` and `message` are the finding's own; each check's
ids and messages are on its page.

Line and column come from `Document.line_col()` applied to the start of
the finding: the line is 1-based, the column 0-based, and every
character, multi-byte or astral, counts as one column. Documents are
read with universal newlines, so `\n`, `\r\n` and a lone `\r` each end
a line, and columns are counted after that translation. The finding's
length is not printed.

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
  points would print different usage text. `--version` prints
  `%(prog)s`, so it reads `tiredize` through both.
- **`--version` reads installed metadata,** because the version
  exists only there: it comes from git tags at build time (see
  [releasing](../operations/releasing.md)). Every published release
  can report what it is.
- **No metadata prints `unknown`, not an error,** so a source tree
  that was never installed still runs, and `--version` never invents a
  number.
- **Three statuses, no more.** Runtime errors share `1` with findings.
  The stream tells them apart: a caller that needs to know reads
  stderr.
