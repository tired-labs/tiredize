---
assignee:
created: 2026-02-28
knowledge: []
priority: medium
status: draft
step:
tags: []
type: spike
workflow: software-engineering
---

# Configuration File Strategy

## Summary

Decide whether to consolidate the three configuration inputs (markdown
schema, frontmatter schema, linter rules) into a single file or keep
them as separate files. Document the decision and implement accordingly.

## Acceptance Criteria

- [ ] Evaluate trade-offs of single file vs separate files
- [ ] Make and document the decision
- [ ] Implement the chosen configuration loading strategy
- [ ] Update CLI argument handling if needed
- [ ] Update relevant specifications

## Design Decisions

Out of scope: new validation features and changes to the validation
logic itself.

## Open Questions

- Separate files allow sharing style rules across projects while
  schemas differ per project. Is this a strong enough reason to keep
  them separate?
- If consolidated, what YAML structure groups the three concerns?
- Should there be a config file discovery mechanism (e.g.,
  `.tiredize.yaml` in project root)?

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Migrated to the v2 issue format during the `.context/` process
    migration. Out of Scope folded into Design Decisions; the v1
    Completion Report was dropped.
