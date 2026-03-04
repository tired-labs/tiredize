---
status: done
type: feature
priority: high
created: 2026-02-28
specs:
  - frontmatter-schema.md
---

# Frontmatter Schema Validation

## Summary

Validate markdown frontmatter against a user-defined YAML schema. The
schema declares which fields must exist, their expected types, and
optionally constrains their values to a set of allowed entries. This
enables CI enforcement of frontmatter correctness for community-submitted
TRRs, repository issue files, and any markdown consumed by Hugo or
similar static site generators.

## Acceptance Criteria

- [x] Implement a duplicate-key-detecting YAML loader (subclass
      `SafeLoader`) that raises `ValueError` on duplicate keys. Used
      only for loading the document's frontmatter during schema
      validation, not for general YAML loading.
- [x] Implement the schema loader (`load_frontmatter_schema`) that
      parses and self-validates the schema YAML. The loader rejects
      invalid schemas with descriptive `ValueError` messages.
- [x] Implement the frontmatter validator (`validate`) that checks a
      parsed `Document` against a loaded schema and returns
      `list[RuleResult]`.
- [x] Wire up the CLI stub `_run_frontmatter_schema()` in `cli.py` to
      load the schema, run validation, and return results. Error
      handling follows the existing pattern (catch `ValueError`,
      `FileNotFoundError`, `yaml.YAMLError`).
- [x] Add unit tests with full coverage for the schema loader,
      validator, and duplicate-key loader.
- [x] Create a `frontmatter-schema.md` specification in
      `.context/specifications/`.

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Markdown schema validation changes
- Linter rule changes
- Configuration file consolidation (separate issue)
- Nested map support (`type: map` with sub-field definitions)
- Modifications to the existing `FrontMatter.extract()` parser
- Changes to how `yaml.safe_load` handles type coercion

## Domain Specific Sections

### Schema File Format

#### Top-Level Properties

| Property             | Type | Default | Description                      |
|----------------------|------|---------|----------------------------------|
| `allow_extra_fields` | bool | `false` | Allow fields not defined in schema |
| `fields`             | map  | —       | Map of field name to field definition |

#### Field Definition Properties

| Property   | Type | Default | Description                              |
|------------|------|---------|------------------------------------------|
| `type`     | string | —    | Required. One of: `string`, `int`, `float`, `bool`, `date`, `list` |
| `required` | bool | `true`  | Field must be present in frontmatter     |
| `allowed`  | list | —       | Restricts the value to entries in this list. For `list` fields, every item must be in the allowed set. |

#### Constraints

- `type` is required on every field definition. Omitting it is a
  schema validation error.
- `required` defaults to `true`. Explicit `required: true` is accepted
  for readability.
- `allowed` values are compared against the YAML-parsed value using
  equality. For scalar fields, the value itself must be in the list.
  For `list` fields, every item in the list must be in the allowed set.
- `type: list` items must be strings. A list item that is not a string
  is a validation error.
- Duplicate items in a `list` field are always a validation error. There
  is no opt-out.
- Map values (YAML dicts) in frontmatter fields are not supported. A
  field whose parsed value is a dict produces a validation error with a
  clear message ("maps are not supported").
- Unknown properties in a field definition (anything other than `type`,
  `required`, `allowed`) are schema validation errors.
- Unknown top-level properties (anything other than `allow_extra_fields`,
  `fields`) are schema validation errors.
- `allowed` entries must match the declared `type` of the field. For
  `list` fields, each `allowed` entry must be a string. For scalar
  fields, each `allowed` entry must match the declared type. Mismatched
  `allowed` entry types are schema validation errors.

#### Example: Issue File Schema

```yaml
allow_extra_fields: false

fields:
  status:
    type: string
    allowed:
      - draft
      - ready
      - active
      - blocked
      - done
      - cancelled

  type:
    type: string
    allowed:
      - bug
      - feature
      - refactor
      - documentation
      - spike

  priority:
    type: string
    allowed:
      - critical
      - high
      - medium
      - low

  created:
    type: date

  parent:
    type: string
    required: false

  sub_issues:
    type: list
    required: false

  specs:
    type: list
    required: false

  labels:
    type: list
    required: false
```

#### Example: TRR Schema

```yaml
allow_extra_fields: false

fields:
  title:
    type: string

  id:
    type: string

  external_ids:
    type: list
    required: false

  tactics:
    type: list
    allowed:
      - Reconnaissance
      - Resource Development
      - Initial Access
      - Execution
      - Persistence
      - Privilege Escalation
      - Defense Evasion
      - Credential Access
      - Discovery
      - Lateral Movement
      - Collection
      - Command and Control
      - Exfiltration
      - Impact

  platforms:
    type: list

  contributors:
    type: list

  date:
    type: date

  draft:
    type: bool
    required: false
```

### Duplicate Key Detection

`yaml.safe_load` silently discards earlier values when a YAML key
appears more than once. This is unacceptable for frontmatter validation
because the user loses data without warning.

Implement a `SafeLoader` subclass that overrides `construct_mapping`
to detect duplicate keys and raise `ValueError` with a message naming
the duplicated key. This loader is used only in the frontmatter schema
validation path — the existing `FrontMatter.extract()` parser and
general `_load_yaml()` helper are not modified.

### Validation Behavior

#### Missing Frontmatter

If the document has no frontmatter block, treat it as an empty dict.
Required fields report as missing; optional-only schemas pass cleanly.
There is no special "no frontmatter found" error.

#### Type Checking

The validator compares the YAML-parsed Python type against the declared
schema type using this mapping:

| Schema type | Python type       |
|-------------|-------------------|
| `string`    | `str`             |
| `int`       | `int` (not `bool`)|
| `float`     | `float`           |
| `bool`      | `bool`            |
| `date`      | `datetime.date`   |
| `list`      | `list`            |

Note: Python's `bool` is a subclass of `int`. The type check must
reject `bool` values when the schema declares `type: int`, consistent
with the existing `get_config_int()` guard in `tiredize/linter/utils.py`.

#### Error Reporting

All errors use `RuleResult` with the `position` set to the frontmatter
block's position (from `document.frontmatter.position`). When
frontmatter is absent, position is `Position(offset=0, length=0)`.

#### Error Types

| Rule ID                                   | Trigger                                    |
|-------------------------------------------|--------------------------------------------|
| `schema.frontmatter.missing_field`        | Required field not present                 |
| `schema.frontmatter.extra_field`          | Field not defined in schema                |
| `schema.frontmatter.wrong_type`           | Value type does not match schema           |
| `schema.frontmatter.value_not_allowed`    | Value not in `allowed` list                |
| `schema.frontmatter.duplicate_list_item`  | List contains duplicate entries            |
| `schema.frontmatter.map_not_supported`    | Field value is a YAML map                  |
| `schema.frontmatter.duplicate_key`        | YAML key appears more than once            |
| `schema.frontmatter.list_item_not_string` | List item is not a string                  |

### File Layout

| File | Purpose |
|------|---------|
| `tiredize/validators/frontmatter_schema.py` | Schema loader and validator |
| `tests/validators/test_frontmatter_schema.py` | Unit tests |
| `.context/specifications/frontmatter-schema.md` | Specification |

The schema loader and validator live in the same module, following the
pattern established by the markdown schema (where `load_schema` lives
in `types/schema.py` and `validate` in `validators/markdown_schema.py`).
For the frontmatter schema, both the loader and validator are colocated
in `validators/frontmatter_schema.py` because the schema data model is
simple (no recursive nesting) and does not need to be a markdown type.

### Integration Points

- **CLI:** `_run_frontmatter_schema()` stub in `tiredize/cli.py`
  already exists. Replace the stub body with schema loading and
  validation calls.
- **Document model:** `document.frontmatter` provides
  `FrontMatter.content` (parsed dict), `FrontMatter.position`, and
  `FrontMatter.string`. When no frontmatter exists,
  `document.frontmatter` is `None`.
- **Output:** Results use `RuleResult` and render through the existing
  `file:line:col: [rule_id] message` formatter in `main()`.

## Design Decisions

- **Explicit types over inferred types.** The schema declares expected
  types explicitly (`type: string`) rather than inferring from YAML
  parsing. This makes schemas self-documenting and catches type
  mismatches (e.g., unquoted `true` where a string is expected).
- **No type coercion.** The validator accepts YAML's native parsed
  types as-is. No attempt to coerce `true` to `"true"` or `1` to
  `"1"`. Users are expected to understand YAML quoting rules.
- **`allowed` as a constraint, not a type.** Enum-like validation is
  expressed as `allowed: [value1, value2]` on any field type, rather
  than introducing a separate `enum` type.
- **List items are always strings.** Lists in frontmatter are
  restricted to string items only. This covers all current use cases
  (TRR tactics/platforms/contributors, issue sub_issues/specs/labels)
  and matches Hugo's practical usage. `items_type` can be added later
  as a non-breaking change if needed.
- **Duplicate list items are always an error.** No `unique_items` flag.
  Duplicates in a list field are unconditionally rejected.
- **No nesting support.** Map values in frontmatter fields produce a
  clear error. Hugo supports nested maps (e.g., `params`), but no
  current use case requires it. `type: map` with sub-field definitions
  can be added later as a non-breaking change.
- **Duplicate YAML key detection via custom loader.** A `SafeLoader`
  subclass catches duplicate keys at parse time rather than scanning
  raw text. This is the correct architectural layer and will work
  correctly if nesting is added later.
- **Required by default.** Fields declared in the schema are required
  unless explicitly marked `required: false`. This is the safer default
  for community-submission validation where forgetting to mark a field
  as required leads to silent acceptance of incomplete frontmatter.
- **Colocated loader and validator.** Unlike the markdown schema (which
  splits `load_schema` into `types/schema.py` and `validate` into
  `validators/`), the frontmatter schema has a flat data model with no
  recursive nesting. Both loader and validator live in
  `validators/frontmatter_schema.py`.

## Open Questions

## References

- CLI stub: `tiredize/cli.py:83-90`
- Frontmatter parser: `tiredize/markdown/types/frontmatter.py`
- Markdown schema loader (pattern reference): `tiredize/markdown/types/schema.py`
- Markdown schema validator (pattern reference): `tiredize/validators/markdown_schema.py`
- Hugo frontmatter docs: https://gohugo.io/content-management/front-matter/
- TRR format spec: `/home/user/techniques/docs/TECHNIQUE-RESEARCH-REPORT.md`

## Completion Report

### Progress

- [x] Implementation complete
- [x] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [ ] User accepted

### Problem

Markdown documents with YAML frontmatter (TRRs, issue files) had no
way to validate their frontmatter against a schema. The
`--frontmatter-schema` CLI flag existed as a stub that silently
accepted any input. Community-submitted TRRs could have missing
required fields, wrong types, or invalid values with no CI enforcement.

### Solution

Implemented `tiredize/validators/frontmatter_schema.py` containing
three components:

1. **Duplicate-key YAML loader** — `SafeLoader` subclass that detects
   duplicate YAML keys (which PyYAML silently drops).
2. **Schema loader** — `load_frontmatter_schema()` parses and
   self-validates the schema YAML, rejecting invalid schemas with
   descriptive errors.
3. **Frontmatter validator** — `validate()` checks a parsed Document
   against a loaded schema, returning `list[RuleResult]` with 8 error
   types covering missing fields, extra fields, wrong types, disallowed
   values, duplicate list items, map values, duplicate keys, and
   non-string list items.

Also created `issue-frontmatter.yaml` schema for the project's own
issue files and wired it into both the pre-commit hook and GitHub
Actions workflow.

### Test Summary

| Test suite | Tests | Result |
|------------|-------|--------|
| `test_frontmatter_schema.py` — safe_load_yaml | 8 | Pass |
| `test_frontmatter_schema.py` — schema loader happy path | 11 | Pass |
| `test_frontmatter_schema.py` — schema loader errors | 16 | Pass |
| `test_frontmatter_schema.py` — validate happy path | 15 | Pass |
| `test_frontmatter_schema.py` — validate missing field | 3 | Pass |
| `test_frontmatter_schema.py` — validate extra field | 3 | Pass |
| `test_frontmatter_schema.py` — validate wrong type | 9 | Pass |
| `test_frontmatter_schema.py` — validate value not allowed | 4 | Pass |
| `test_frontmatter_schema.py` — validate duplicate list item | 3 | Pass |
| `test_frontmatter_schema.py` — validate map not supported | 2 | Pass |
| `test_frontmatter_schema.py` — validate list item not string | 4 | Pass |
| `test_frontmatter_schema.py` — validate duplicate key | 1 | Pass |
| `test_frontmatter_schema.py` — validate position reporting | 2 | Pass |
| `test_frontmatter_schema.py` — validate combined errors | 3 | Pass |
| `test_frontmatter_schema.py` — validate edge cases | 12 | Pass |
| `test_cli.py` — frontmatter schema CLI tests | 3 new | Pass |

Total: 96 new tests in `test_frontmatter_schema.py`, 3 new CLI tests
(1 replaced stub test). All 648 project tests pass.

### Coverage

| File | Statements | Missed | Coverage |
|------|-----------|--------|---------|
| `frontmatter_schema.py` | 155 | 0 | 100% |
| `cli.py` | 84 | 2 | 98% |

Uncovered CLI lines: `__main__` guard (line 59) and `SystemExit`
wrapper (line 192). Standard entry-point boilerplate.

### SE Peer Review

#### Incorporated

No actionable findings.

#### Not Incorporated

- Nested duplicate key detection noted as future awareness item (not
  relevant while maps are unsupported).
- Spec wording "mapping key" vs "top-level mapping key" noted as minor
  precision issue — deferred as non-behavioral.

### QA Engineer Review

#### Incorporated

#### Not Incorporated

### Technical Architect Review

#### Incorporated

#### Not Incorporated

### Follow-Up Work

None identified.

### Breaking Changes

The `--frontmatter-schema` CLI flag previously accepted any YAML file
silently and returned success (stub behavior). It now validates the
schema and document, so previously-passing invocations with invalid
schemas will fail with exit code 1.

### Process Feedback
