# tiredize Wiki

Tiredize is a schema-driven markdown validator and linter. It parses
markdown into typed elements and checks documents against user-defined
YAML: a markdown schema for section structure, a frontmatter schema for
YAML fields, and linter rules for style. It was built for TIRED Labs'
Technique Research Reports and works for any structured markdown. This
wiki describes how tiredize works now, why, and how it is changed. The
user guide is the repository's `README.md`.

## Pages

- [Glossary](./glossary.md): terms used across the wiki.

### Overview

- [Scope](./overview/scope.md): the problem, the users, and what each
  kind of check owns.

### Repository

- [Repository layout](./repository/layout.md): where code, tests,
  configuration and workflows live, and file conventions.

### Architecture

- [Pipeline](./architecture/pipeline.md): how a run flows through the
  components, the shared result types, and findings versus errors.

### Components

- [Command-line interface](./components/cli.md): arguments, exit
  status, output streams and processing order.
- [Markdown parser](./components/markdown-parser.md): the document
  model, element patterns, the sanitize chain and known GFM gaps.
- [Autolinks](./components/autolinks.md): the GFM autolink rules, the
  readings where GFM is silent, and divergences from `cmark-gfm`.
- [Linter engine](./components/linter-engine.md): rule discovery,
  configuration validation, the element vocabulary and URL checking.
- [Linter rules](./components/linter-rules.md): the built-in rules
  and their configuration.
- [Markdown schema validator](./components/markdown-schema-validator.md):
  the schema format and the ordered and unordered algorithms.
- [Frontmatter schema validator](./components/frontmatter-schema-validator.md):
  the frontmatter schema format and its checks.

### Operations

- [Installing and running](./operations/installing-and-running.md):
  installing, invoking, and gating hooks and CI on the exit status.
- [Releasing](./operations/releasing.md): versioning and the TestPyPI
  release workflow.

### Practices

- [Testing](./practices/testing.md): how to run the tests and the rules
  every test follows.
- [Continuous integration](./practices/ci.md): what GitHub Actions runs.
- [Contributing](./practices/contributing.md): what a pull request needs
  and how it is reviewed.
