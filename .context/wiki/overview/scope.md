# Scope

## Overview

Tiredize is a schema-driven markdown validator and linter. It parses a
markdown document into typed elements, then checks it against
user-defined YAML: a markdown schema for its section structure, a
frontmatter schema for its YAML fields, and a rules file for style.

It was built for the Technique Research Reports (TRRs) TIRED Labs
publishes in its techniques repository. A TRR follows a rigid structure:
named sections in a fixed order, required frontmatter fields and
consistent formatting. No existing markdown linter could enforce a
structural schema. Tiredize catches a missing or misnamed section before
peer review, and it replaced the structural half of an earlier Go tool,
`trrlint`. The TRR schema itself lives in the techniques repository, not
here.

Tiredize is general-purpose and open source. Every document shape is
defined in external configuration, so any project with predictably
structured markdown (runbooks, reports, issue files) can use it. The
primary users are TIRED Labs contributors and reviewers.

## Design Boundary

Tiredize validates structure and style, not meaning.

- **Structure** (sections exist, in order, at the right heading level,
  within repeat bounds) belongs to the [markdown schema
  validator](../components/markdown-schema-validator.md).
- **Frontmatter fields** (present, typed, allowed values) belong to the
  [frontmatter schema
  validator](../components/frontmatter-schema-validator.md).
- **Style and formatting** (line length, whitespace, allowed elements,
  reachable links) belong to [linter rules](../components/linter-rules.md).
- **Content** is out of scope: what a section says, and whether
  sections agree with each other.

## Design Decisions

- **Structure in the schema, style in the linter.** Each check has one
  home, so a schema reads as the document's outline and a rules file as
  its house style. Separate files also let one style be shared across
  projects whose schemas differ.
- **Schemas are explicit.** A schema describes the whole document;
  there is no "stop checking below here" setting, because such a schema
  no longer describes the document. An `allow_subsections` key was
  declined for this reason.
- **Element recognition aims to match GitHub.** A user should be able
  to predict from GitHub's rendering what tiredize sees, so where the
  parser follows GFM it follows it exactly (see
  [autolinks](../components/autolinks.md)); elsewhere the gaps are listed
  on the [parser](../components/markdown-parser.md) page.
