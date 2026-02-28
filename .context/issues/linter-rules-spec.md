Status: draft

# Document Built-in Linter Rules as Individual Specifications

## Summary

The linter specification (`linter.md`) documents the engine, discovery
mechanism, config helpers, and rule module convention, but does not
document what each built-in rule actually does. Each rule is a
self-contained plugin with its own config contract, validation logic,
and edge case behavior. Each deserves its own specification file.

## Acceptance Criteria

- [ ] Create `.context/specifications/linter-rule-line-length.md`
      documenting: config keys (types, defaults, descriptions),
      validation logic, violation output, edge cases (CRLF handling,
      empty lines, boundary at exact limit)
- [ ] Create `.context/specifications/linter-rule-tabs.md`
      documenting: config keys, validation logic, violation output,
      edge cases (multiple tabs per line, tab position tracking, CRLF)
- [ ] Create `.context/specifications/linter-rule-trailing-whitespace.md`
      documenting: config keys, validation logic, violation output,
      edge cases (whitespace-only lines, mixed spaces/tabs, CRLF)
- [ ] Create `.context/specifications/linter-rule-links.md`
      documenting: config keys, which link types are checked (inline,
      bracket, bare, reference definitions), delegation to
      `check_url_valid`, violation output, edge cases (disabled
      validation, missing config)
- [ ] Verify documented behavior matches actual code behavior (spec
      fidelity check against source)
- [ ] Update `.context/specifications/linter.md` to reference the
      individual rule specs from the File Layout or a new "Built-in
      Rules" section

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Rule code changes
- New rules
- Engine, discovery, or config helper changes

## Design Decisions

- Each rule gets its own spec file rather than a shared
  `linter-rules.md` or a section in `linter.md`. Rules are
  self-contained plugins loaded by the engine, not components of it.
  Individual files scale naturally as new rules are added and give
  complex rules (like links) room for detailed documentation.

## Open Questions

- Should the spec document the exact error message format for each
  rule, or just the semantic meaning? Exact messages are brittle to
  maintain but useful for testing.
