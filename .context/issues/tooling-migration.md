---
status: draft
type: refactor
priority: low
created: 2026-02-28
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

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Code logic changes
- New features or bug fixes bundled with the migration

## Design Decisions

## Open Questions

- Does Ruff cover all flake8 rules currently in use, or are there gaps?
- Should the import migration happen in one commit or file-by-file?

## Completion Report

This issue predates the current issue file format. Completion report
sections will be populated if the issue is revisited.

### Progress

- [ ] Implementation complete
- [ ] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [ ] User accepted

### Problem

### Solution

### Test Summary

### Coverage

### SE Peer Review

#### Incorporated

#### Not Incorporated

### QA Engineer Review

#### Incorporated

#### Not Incorporated

### Technical Architect Review

#### Incorporated

#### Not Incorporated

### Follow-Up Work

### Breaking Changes

### Process Feedback
