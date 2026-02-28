Status: draft

# Frontmatter Schema Validation

## Summary

Design and implement validation of markdown frontmatter against a
user-defined schema. The `--frontmatter-schema` CLI flag exists with
a stub handler in `cli.py`. This feature validates required fields,
accepted types, and accepted values to make TRRs programmatically
parsable for web frontends.

## Acceptance Criteria

- [ ] Design the frontmatter schema YAML format (fields, types,
      constraints, required/optional)
- [ ] Implement the schema loader with input validation
- [ ] Implement the frontmatter validator
- [ ] Wire up the CLI stub in `_run_frontmatter_schema()`
- [ ] Add unit tests with full coverage
- [ ] Update the markdown-schema-validator specification or create a
      new frontmatter-schema specification

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Markdown schema validation changes
- Linter rule changes
- Configuration file consolidation (separate issue)

## Design Decisions

## Open Questions

- What types should the schema support? (string, int, bool, list,
  date, enum?)
- Should the schema support nested frontmatter fields (e.g., YAML
  maps within maps)?
- How should type coercion work for YAML values that could be
  ambiguous (e.g., `true` as bool vs string)?

## References

- CLI stub: `tiredize/cli.py`
- Frontmatter parser: `tiredize/markdown/types/frontmatter.py`
- TRR format spec: `/home/user/techniques/docs/TECHNIQUE-RESEARCH-REPORT.md`
