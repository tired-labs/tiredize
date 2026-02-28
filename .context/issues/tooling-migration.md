Status: draft

# Tooling Migration

## Summary

Evaluate replacing flake8 with Ruff as the project linter and migrate
existing code to PEP 8 import grouping with section comments.

## Acceptance Criteria

- [ ] Investigate Ruff as a flake8 replacement -- compare features,
      configuration, and migration path
- [ ] If approved, replace flake8 with Ruff in CI and development
      dependencies
- [ ] Migrate all source and test files to PEP 8 import grouping
      (blank lines between stdlib, third-party, and local groups with
      section comments)

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
