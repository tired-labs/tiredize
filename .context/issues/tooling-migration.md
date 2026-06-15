---
assignee:
created: 2026-02-28
knowledge: []
priority: low
status: draft
step:
tags: []
type: refactor
workflow: software-engineering
---

# Tooling Migration

## Summary

Evaluate replacing flake8 with Ruff as the project linter, migrate
existing code to PEP 8 import grouping with section comments, and
declare development dependencies in `pyproject.toml` so they can be
installed via `pip install -e ".[dev]"`.

## Acceptance Criteria

- [ ] Investigate Ruff as a flake8 replacement -- compare features,
      configuration, and migration path
- [ ] If approved, replace flake8 with Ruff in CI and development
      dependencies
- [ ] Migrate all source and test files to PEP 8 import grouping
      (blank lines between stdlib, third-party, and local groups with
      section comments)
- [ ] Declare development dependencies in `pyproject.toml` under
      `[project.optional-dependencies]` or `[tool.hatch.envs]` so
      `pip install -e ".[dev]"` works

## Design Decisions

Out of scope: code logic changes, and new features or bug fixes bundled
with the migration.

## Open Questions

- Does Ruff cover all flake8 rules currently in use, or are there gaps?
- Should the import migration happen in one commit or file-by-file?

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Migrated to the v2 issue format during the `.context/` process
    migration. Out of Scope folded into Design Decisions; the v1
    Completion Report was dropped.
