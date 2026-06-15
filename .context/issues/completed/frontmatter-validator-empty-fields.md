---
assignee:
created: 2026-06-15
knowledge: []
priority: medium
status: done
step:
tags: [frontmatter-validator, validation]
type: feature
workflow: software-engineering
---

# Frontmatter Validator: Treat Empty Optional Fields as Absent

## Summary

The frontmatter schema validator did no type coercion and had no
null/empty handling, so a present-but-blank optional field (for example
`assignee:`, which YAML parses as `None`) failed its `type` check with
`wrong_type`. The issue-file convention in both this repository and the
dotclaude config repository leaves optional fields such as `assignee` and
`step` blank until they are populated. The validator now treats a
present-but-empty or null value for a non-required field as absent, so
blank optional fields validate cleanly.

## Acceptance Criteria

- [x] A non-required field whose value is null or empty passes validation
      (treated as absent)
- [x] A required field whose value is null or empty still fails, with a
      clear error
- [x] The behavior is documented in the frontmatter-schema-validator
      specification
- [x] Unit tests cover: blank optional string field, blank required
      field, empty list, and a populated field
- [x] dotclaude-style issue frontmatter with blank `assignee:` and
      `step:` validates cleanly against the issue frontmatter schema

## Design Decisions

A present field whose value is YAML null is treated as "not provided":
reported `missing_field` when required, ignored when optional. Empty
handling is always-on for non-required fields rather than a per-field
`nullable` flag — the simplest option, and it matches the convention of
leaving optional frontmatter fields blank until populated.

## Open Questions

None — resolved (see Design Decisions).

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Found during the tiredize `.context/` readiness assessment while
    checking why self-validation was not running locally.

### 2026-06-15T12:00:00+00:00

Author: program-manager

    Implemented directly as part of the `.context/` migration PR rather
    than via the workflow pipeline (the user chose to pull the fix in so
    the migrated issues' blank optional fields would validate). The fix
    lives in `tiredize/validators/frontmatter_schema.py` with tests in
    `tests/validators/test_frontmatter_schema.py` and a spec update.
    Marked done.
