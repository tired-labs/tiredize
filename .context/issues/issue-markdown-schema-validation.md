# Implement Markdown Schema Validation

## Summary

Add the ability to validate a markdown document's structure against a
user-defined schema. The schema defines which sections must exist, their
heading levels, their ordering, and whether they are required or optional.

This feature replaces the structural validation half of the existing
Go-based `trrlint` in the TIRED Labs techniques repository, while being
general-purpose enough for any markdown document that follows a
predictable structure.

## Motivation

- Contributors to TIRED Labs TRRs frequently forget sections, misname
  them, or add sections that don't belong. Schema validation catches
  these issues before peer review.
- The tool is not TRR-specific. Any team producing structured markdown
  (red team deliverables, internal documentation, runbooks) benefits
  from enforcing consistent structure.
- Linting for structure issues early in the workflow eliminates 90% of
  formatting feedback during review.

## Design Principles

- **Schema validates structure, linter rules validate content.** The
  schema engine checks that sections exist, are in the right order, at
  the right heading level. Anything about what's *inside* a section
  (table contents, link formats, required fields) belongs in a linter
  rule.
- **Start with section-level validation (Option A), design for child
  element validation (Option B) later.** The initial implementation
  validates sections only. The architecture should not preclude adding
  "this section must contain a table" or "this section must contain a
  bulleted list" in a future iteration.
- **Content validation (Option C) is out of scope.** Checking specific
  values inside tables or correlating content across sections is linter
  rule territory.

## Schema File Format

The schema is a YAML file passed to the CLI via `--markdown-schema`.

### Top-Level Properties

| Property               | Type | Default | Description                    |
|------------------------|------|---------|--------------------------------|
| `enforce_order`        | bool | `true`  | Validate section ordering      |
| `allow_extra_sections` | bool | `false` | Allow sections not in schema   |
| `sections`             | list | —       | Ordered list of section defs   |

### Section Definition Properties

| Property   | Type        | Default        | Description                     |
|------------|-------------|----------------|---------------------------------|
| `name`     | string      | —              | Exact section header match      |
| `pattern`  | string      | —              | Regex pattern for header match  |
| `level`    | int         | parent + 1     | Required heading level (1-6)    |
| `required` | bool        | `true`         | Section must be present         |
| `repeat`   | bool or map | —              | Section may appear repeatedly   |
| `sections` | list        | —              | Nested child section defs       |

**Constraints:**

- Exactly one of `name` or `pattern` must be present. Both or neither
  is an error.
- `level` is optional. When omitted, it is inferred as the parent
  section's level + 1. Top-level sections with no parent default to 1.
  When present, the loader validates it is consistent with nesting
  depth.
- When `required` is omitted, it defaults to `true`.
- `repeat: true` means one or more occurrences with no upper bound.
- `repeat: {min: N, max: N}` sets explicit bounds. `min` defaults to 1
  if omitted. `max` defaults to no limit if omitted.
- `sections` defines child sections nested under this section. Children
  are validated within the scope of their parent. Nesting in the schema
  mirrors nesting in the document.
- Sections not declared in the schema are considered unexpected. When
  `allow_extra_sections: false` (default), unexpected sections produce
  an error.

### Example: TRR Schema

```yaml
enforce_order: true
allow_extra_sections: false
sections:
  - pattern: ".+"
    sections:
      - name: "Metadata"
        level: 2
        sections:
          - name: "Scope Statement"
            level: 3
            required: false
      - name: "Technique Overview"
        level: 2
      - name: "Technical Background"
        level: 2
      - name: "Procedures"
        level: 2
        sections:
          - pattern: "Procedure [A-Z]: .+"
            level: 3
            repeat: true
            sections:
              - name: "Detection Data Model"
                level: 4
      - name: "Available Emulation Tests"
        level: 2
      - name: "References"
        level: 2
```

## Validation Algorithm

### Ordered Mode (`enforce_order: true`)

Ordering is enforced among sibling sections under the same parent,
not across nesting levels. When the validator matches a parent
section, it recurses into that parent's children and validates them
independently.

Walk the document sections and schema sections in parallel using two
pointers:

1. If the current document section matches the current schema entry,
   advance both pointers.
2. If the current document section matches a *later* schema entry and
   all skipped schema entries are `required: false`, skip the optional
   entries and advance to the match.
3. If the current document section matches a later schema entry but a
   skipped entry is `required: true`, emit an error for the missing
   required section.
4. If the current document section matches nothing in the schema and
   `allow_extra_sections: false`, emit an error for the unexpected
   section.
5. At end of document, emit errors for any remaining `required: true`
   schema entries not yet matched.
6. At end of document, remaining `required: false` entries are silently
   accepted.

For `repeat` sections: when a match occurs, keep the schema pointer on
the same entry until the next document section no longer matches. Then
check that the match count satisfies `min`/`max` bounds before
advancing.

**Nested repeat groups:** Children of a repeating section are defined
via the `sections` field on that entry. Each instance of the parent
must independently satisfy all child section requirements. For
example, if Procedure (H3) repeats 3 times and has a required
Detection Data Model (H4) child, the validator expects 3 DDMs — one
per Procedure instance.

### Unordered Mode (`enforce_order: false`)

1. Check that every `required: true` schema entry has at least one
   matching section in the document.
2. If `allow_extra_sections: false`, check that every document section
   matches at least one schema entry.
3. For `repeat` entries, validate match count against `min`/`max`.

### Matching Rules

- `name`: case-sensitive exact match against the section header title.
- `pattern`: full-match regex against the section header title.
- `level`: heading level must match exactly.

## Error Output

All errors follow the existing linter output format:

```
file:line:col: [schema.markdown.<error_type>] <message>
```

### Error Types

| Rule ID                                | Trigger                        |
|----------------------------------------|--------------------------------|
| `schema.markdown.missing_section`      | Required section not found     |
| `schema.markdown.unexpected_section`   | Section not defined in schema  |
| `schema.markdown.wrong_level`          | Heading level mismatch         |
| `schema.markdown.out_of_order`         | Section in wrong position      |
| `schema.markdown.repeat_below_minimum` | Fewer occurrences than min     |
| `schema.markdown.repeat_above_maximum` | More occurrences than max      |

## Integration Points

- **CLI:** The `--markdown-schema` flag already exists with a
  placeholder in `_run_markdown_schema()`. The implementation replaces
  the placeholder.
- **Output:** Results are returned as `list[RuleResult]` and rendered
  by the same `file:line:col` formatting as linter rules.
- **Document model:** The parsed `Document` already provides
  `document.sections` with `section.header.title`,
  `section.header.level`, `section.header.position`, and
  `section.subsections` — the recursive structure mirrors the nested
  schema, allowing the validator to walk both trees in parallel.

## Design Decisions

- **Schema self-validation:** The loader validates the schema file
  itself (e.g., rejects a schema with both `name` and `pattern`)
  before running document validation, with clear error messages.

## Open Questions

None at this time.

## Progress

### Completed

- **Data model:** `SchemaConfig` and `SchemaSection` frozen dataclasses
  in `tiredize/markdown/types/schema.py`. Nested `sections` field
  mirrors the document's recursive `subsections` structure.
- **Schema loader:** `load_schema(yaml_string) -> SchemaConfig` in the
  same module. Handles level inference (parent + 1), repeat
  normalization, and schema self-validation (name/pattern conflicts,
  invalid child levels). 100% test coverage.
- **Parser bugfix:** Fixed `Section._map_subsections` to build a clean
  tree — grandchildren no longer leak into grandparent subsections.
  Added 6 tests in `tests/markdown/types/test_section.py`.
- **Document validation — ordered mode:** `validate(document, schema)`
  in `tiredize/validators/markdown_schema.py`. Recursive two-pointer
  walk that matches document sections against schema sections at each
  nesting level. Handles missing, unexpected, out-of-order, wrong
  level, and repeat bound violations.
- **Document validation — unordered mode:** `_validate_unordered` in
  the same module. Iterates schema entries, claims matching doc
  sections via index set, checks required/unexpected/repeat bounds.
  Recurses into children for both repeat and non-repeat entries.
- **Ambiguity detection:** `AmbiguityError` raised in both ordered and
  unordered modes when a document section matches multiple sibling
  schema entries (e.g., a catch-all pattern alongside a specific
  name). Fails fast before any validation logic runs.
- **Full requirements coverage audit:** 34 tests in
  `tests/validators/test_markdown_schema.py` covering all issue
  requirements across both modes, including matching rule edge cases
  (case sensitivity, full-match regex). 99% coverage (1 unreachable
  defensive line).

- **CLI integration:** `_run_markdown_schema()` in `tiredize/cli.py`
  wired up. Reads the schema file, calls `load_schema()` and
  `validate()`, returns results. Invalid schemas (`ValueError`) and
  ambiguous schemas (`AmbiguityError`) are caught gracefully — printed
  to stderr with exit code 1. Validation errors print all results in
  the standard `file:line:col: [rule_id] message` format.

### Next

- Feature complete. No remaining implementation work.

## Out of Scope

- Content validation within sections (table fields, link formats).
  These belong in linter rules.
- Frontmatter schema validation (separate feature, separate flag).
- Cross-section content correlation (e.g., Procedures table rows
  matching subsection names). This is linter rule territory.

## References

- TRR format specification: `/home/user/techniques/docs/TECHNIQUE-RESEARCH-REPORT.md`
- TRR template: `/home/user/techniques/docs/examples/trr0000/win/README.md`
- TRR style guide: `/home/user/techniques/docs/STYLE-GUIDE.md`
- Existing Go linter: `/home/user/techniques/tools/trrlint/main.go`
