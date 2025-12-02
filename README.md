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

- [x] Frontmatter Content Extraction
- [ ] Markdown Content Extraction
  - [x] Sections
    - [x] Headers
    - [x] Links
      - [x] Inline
      - [x] Reference-style
      - [x] Bracket Links
      - [x] Bare
    - [ ] References/Footnotes
    - [x] Images
      - [x] Inline
      - [x] Reference-style
    - [x] Code blocks
      - [x] Inline
      - [x] Fenced
    - [x] Block quotes
    - [ ] Lists
      - [ ] Ordered
      - [ ] Unordered
    - [ ] Tables
- [ ] Linter Rule Engine
  - [ ] Frontmatter Schema
  - [ ] Markdown Scheme
  - [ ] Line Length
  - [ ] Whitespace
  - [ ] Link Validation
  - [ ] Markdown styling
    - [ ] Lists
    - [ ] Links
    - [ ] Headers
    - [ ] Code Blocks
    - [ ] Tables
    - [ ] References/Footnotes

Future releases will expand support for additional [TIRED Labs] document formats
and deeper structural analysis.

## Status

Tiredize is in active development. The current focus is defining the project
structure, implementing the core document parser, and building the initial
validator set that supports one canonical document type.

## Usage

Once packaged, Tiredize will be installed via pip and run from the command line:

```bash
tiredize --frontmatter frontmatter_schema.yml --markdown markdown_schema.yml --rules linter_rules.yml markdown_file.md 
```

The command prints rule violations and returns a nonzero exit code when
validation fails, making it suitable for pre-commit hooks and CI/CD pipelines.

## License

TBD

[TIRED Labs]: https://www.tired-labs.org/
[Technique Research Reports]: https://github.com/tired-labs/techniques
