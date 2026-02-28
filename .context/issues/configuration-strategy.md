Status: draft

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

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- New validation features
- Changes to the validation logic itself

## Design Decisions

## Open Questions

- Separate files allow sharing style rules across projects while
  schemas differ per project. Is this a strong enough reason to keep
  them separate?
- If consolidated, what YAML structure groups the three concerns?
- Should there be a config file discovery mechanism (e.g.,
  `.tiredize.yaml` in project root)?
