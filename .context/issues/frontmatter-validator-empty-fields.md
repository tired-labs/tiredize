---
assignee:
created: 2026-06-14
knowledge: []
priority: medium
status: draft
step:
tags: [frontmatter-validator, validation]
type: feature
workflow: software-engineering
---

# Frontmatter Validator: Treat Empty Optional Fields as Absent

## Summary

The frontmatter schema validator does no type coercion and has no
null/empty handling, so a present-but-blank optional field (for example
`assignee:`, which YAML parses as `None`) fails its `type` check with
`wrong_type`. The issue-file convention in both this repository and the
dotclaude config repository leaves optional fields such as `assignee` and
`step` blank until they are populated. The validator should treat a
present-but-empty or null value for a **non-required** field as absent,
so blank optional fields validate cleanly.

## Acceptance Criteria

- [ ] A non-required field whose value is null or empty passes validation
      (treated as absent)
- [ ] A required field whose value is null or empty still fails, with a
      clear error
- [ ] The behavior is documented in the frontmatter-schema-validator
      specification
- [ ] Unit tests cover: blank optional string field, blank required
      field, empty list, and a populated field
- [ ] dotclaude-style issue frontmatter with blank `assignee:` and
      `step:` validates cleanly against the issue frontmatter schema

## Design Decisions

<!-- To be filled during scoping. -->

## Open Questions

- Should empty handling be configurable per field (an explicit
  `nullable: true`), or always allowed for non-required fields? Current
  lean: always allowed for non-required fields — simplest, and matches
  the issue-file convention.

## Comments

### 2026-06-14T00:00:00+00:00

Author: program-manager

    Captured during the tiredize `.context/` readiness assessment. The
    blank `assignee:`/`step:` convention used by dotclaude issues fails
    the current validator, which would block dogfooding tiredize against
    dotclaude (see dotclaude issue tiredize-markdown-validation-ci).
    Chosen as the first issue to exercise the new software-engineering
    workflow once the assessment is complete.
