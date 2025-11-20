# Tiredize

[![Run tests and upload coverage](https://github.com/tired-labs/tiredize/actions/workflows/ci.yaml/badge.svg)](https://github.com/tired-labs/tiredize/actions/workflows/ci.yaml)  [![Coverage Status](https://coveralls.io/repos/github/tired-labs/tiredize/badge.svg)](https://coveralls.io/github/tired-labs/tiredize)

Tiredize is a schema driven markdown validation tool that ensures [TIRED Labs]
documentation adheres to consistent structural and formatting requirements. It
provides a configurable rules engine that can enforce front matter schemas,
heading patterns, table structures, list styles, and link conventions for any
defined document type.

## Overview

Markdown is flexible, but [TIRED Labs] documentation often depends on
predictable structure. [Technique Research Reports], Detection Documents, and
other deliverables follow specific conventions that enable reliable indexing,
automated processing, and downstream tooling. Tiredize validates these
conventions by combining custom parsing logic with document type specific
schemas.

## Features

Tiredize is early in development, but the initial goals include:

- [ ] Schema validation of front matter fields and types.
- [ ] Enforcement of required headings and section ordering.
- [ ] Structural checks on tables, including header rows and column consistency.
- [ ] Enforcement of list marker style and line length requirements.
- [ ] Validation of link formatting and availability.
- [ ] Configurable rule sets per document type, driven by YAML schemas.

Future releases will expand support for additional [TIRED Labs] document formats
and deeper structural analysis.

## Status

Tiredize is in active development. The current focus is defining the project
structure, implementing the core document parser, and building the initial
validator set that supports one canonical document type.

## Usage

Once packaged, Tiredize will be installed via pip and run from the command line:

```bash
tiredize --schema path/to/schema.yml path/to/document.md 
```

The command prints rule violations and returns a nonzero exit code when
validation fails, making it suitable for pre-commit hooks and CI/CD pipelines.

## License

TBD

[TIRED Labs]: https://www.tired-labs.org/
[Technique Research Reports]: https://github.com/tired-labs/techniques
