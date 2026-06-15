---
assignee: PM
created: 2026-06-14
knowledge: []
priority: high
status: in-progress
step:
tags: [process-migration, v2]
type: refactor
workflow: to-be-determined
---

# Migrate .context/ to the v2 Process

## Summary

Bring tiredize's `.context/` into line with the refactored (v2) dotclaude
process: adopt the new issue format (frontmatter and sections), archive
completed issues, migrate the active drafts, wire workflow routing, and
align the supporting docs. tiredize's `.context/` was built under the old
issue model, and its local schema and spec now contradict the canonical
dotclaude templates. This issue tracks the migration so the work rides a
compliant `issues/` branch rather than an ad-hoc maintenance branch.

## Acceptance Criteria

- [x] Issue frontmatter schema rewritten to the v2 format (statuses,
      fields, alphabetized; `assignee`/`step` optional; `workflow`
      includes the `to-be-determined` sentinel)
- [x] Issue markdown (section) schema rewritten to the v2 five-section
      shape
- [x] `issue-file-format` spec removed from tiredize (it describes a
      cross-project standard, not a tiredize subsystem); canonical spec
      authoring tracked in dotclaude `issue-format-specification`
- [x] `.context/issues/completed/` created; the 19 done issues (plus the
      now-complete `frontmatter-validator-empty-fields`) moved there
- [x] The 8 active drafts migrated to v2 frontmatter and sections
- [x] `AGENTS.md` knowledge mapping added for the software-engineering
      workflow steps
- [x] `PROJECT.md` aligned to `templates/PROJECT.md`
- [x] `.context/specifications/` aligned to `templates/SPECIFICATION.md`
      (`frontmatter-schema-validator` File Layout reordered; others
      already conformed)
- [x] Migrated issues validate against the new schemas

## Design Decisions

- Adopt the dotclaude templates as canonical; rewrite tiredize's local
  validation schemas to the v2 format (dogfooding).
- The `issue-file-format` spec describes a cross-project standard, not a
  tiredize subsystem, so it was removed from tiredize and its authoring
  moved to dotclaude (`issue-format-specification`); the schema headers
  now point at the standard.
- The `frontmatter-validator-empty-fields` fix was implemented inline in
  this PR (not via the workflow pipeline) so migrated issues' blank
  optional fields validate.
- Done issues are archived as-is to `completed/`, not migrated.
- Canonical schema content authored here can later be lifted into
  dotclaude (see dotclaude issue `tiredize-markdown-validation-ci`).
- The validator "aligns up": blank optional fields will be supported (see
  `frontmatter-validator-empty-fields`) rather than omitting the fields.
- `workflow` stays required; edge cases that do not yet fit a pipeline
  use the `to-be-determined` sentinel rather than omitting the field.

## Open Questions

- `linter-rules-spec` routing depends on the technical-documentation
  workflow (tracked in dotclaude) being defined.

## Comments

### 2026-06-14T00:00:00+00:00

Author: program-manager

    Created mid-migration to track work that was already in progress, so
    it rides a compliant `issues/context-process-migration` branch. The
    `workflow` is `to-be-determined`: this is PM-led maintenance that
    fits neither existing pipeline yet.
