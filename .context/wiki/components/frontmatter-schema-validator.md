# Frontmatter Schema Validator

## Overview

The frontmatter schema validator checks a document's YAML frontmatter
against a user-defined schema. It validates field presence, types, and
value constraints. Located in `tiredize/validators/frontmatter_schema.py`.
It reads the frontmatter the [markdown parser](./markdown-parser.md)
extracts. It exists so CI can enforce frontmatter on submitted TRRs and
on any markdown read by a static site generator.

## Contracts and Interfaces

### Public API

```python
# tiredize/validators/frontmatter_schema.py
def validate(
    document: Document,
    schema: FrontmatterSchema,
) -> list[RuleResult]:
```

Validates the document's frontmatter against the schema. Returns a list
of `RuleResult` instances with rule IDs from the error types table below.

### Schema Loader

```python
# tiredize/validators/frontmatter_schema.py
def load_frontmatter_schema(yaml_string: str) -> FrontmatterSchema:
```

Parses a YAML string into a `FrontmatterSchema`. Validates the schema
itself before returning: required `fields` key, valid type declarations,
`allowed` value type consistency, and unknown property rejection. Raises
`ValueError` for all validation failures.

### Duplicate Key Loader

```python
# tiredize/validators/frontmatter_schema.py
def safe_load_yaml(text: str):
```

Parses YAML with duplicate key detection. Raises `ValueError` when a
mapping key appears more than once. Uses a `SafeLoader`
subclass with a custom constructor for `DEFAULT_MAPPING_TAG` that
calls `construct_pairs` to detect duplicates before building the dict.
Used in both the schema loader and the frontmatter validation path.

### Data Model

```python
# tiredize/validators/frontmatter_schema.py
@dataclass(frozen=True)
class FieldSchema:
    type: str
    required: bool = True
    allowed: list | None = None

@dataclass(frozen=True)
class FrontmatterSchema:
    allow_extra_fields: bool = False
    fields: dict[str, FieldSchema] = field(default_factory=dict)
```

## File Layout

| File                                          | Purpose                    |
|-----------------------------------------------|----------------------------|
| `tiredize/validators/frontmatter_schema.py`   | Schema loader and validator |
| `tests/validators/test_frontmatter_schema.py` | Unit tests                 |

## Schema File Format

The file must be a YAML mapping. Any key not listed below, at the top
level or in a field definition, is rejected, as is a key that appears
twice. Every fault in the schema file raises `ValueError` before any
document is checked, which the [CLI](./cli.md) reports as a runtime
error. An empty file is rejected, because `fields` is required.

### Top-Level Keys

| Key                  | Type    | Required | When absent | Accepted values |
|----------------------|---------|----------|-------------|-----------------|
| `fields`             | mapping | yes      | —           | Field name to field definition; `{}` is allowed. Names must be strings, so quote a name YAML would read as another type (`"true"`, `"42"`) |
| `allow_extra_fields` | bool    | no       | `false`     | `true` accepts frontmatter fields the schema does not define |

### Field Definition Keys

| Key        | Type   | Required | When absent | Accepted values |
|------------|--------|----------|-------------|-----------------|
| `type`     | string | yes      | —           | `string`, `int`, `float`, `bool`, `date`, `list` |
| `required` | bool   | no       | `true`      | `false` lets the field be absent or null |
| `allowed`  | list   | no       | any value of the type | A non-empty list. Entries must have the field's type (strings for a `list` field), with the same guards as values: no `bool` for `int`, no `int` for `float`, no timestamp for `date` |

### Type Mapping

| Schema type | Python type        |
|-------------|--------------------|
| `string`    | `str`              |
| `int`       | `int` (not `bool`) |
| `float`     | `float` (not `int`) |
| `bool`      | `bool`             |
| `date`      | `datetime.date` (not `datetime.datetime`) |
| `list`      | `list` of strings  |

### Constraints

- `allowed` values are compared using equality. For scalar fields, the
  value itself must be in the list. For `list` fields, every item must
  be in the list.
- `type: list` items must be strings, and duplicate items are always
  rejected.
- Map values (YAML mappings) are never accepted as field values; they
  report `map_not_supported`.

## Validation Behavior

### Missing Frontmatter

If the document has no frontmatter block, the validator treats it as
an empty dict. Required fields report as missing; optional-only schemas
pass cleanly. A frontmatter block whose YAML does not parse is treated
the same way, because the parser drops it (see [markdown
parser](./markdown-parser.md)); no YAML error is reported.

Frontmatter that parses to something other than a mapping, such as a
list, reports `wrong_type` and is then treated as empty.

Every finding points at the frontmatter block, or at offset 0 when
there is none.

### Empty Field Values

A field that is present but has an empty (YAML `null`) value — for
example a bare `assignee:` line — is treated as **not provided**. A
required field with a null value reports `missing_field`; an optional
(`required: false`) field with a null value passes with no error and is
not type-checked. This supports the convention of leaving optional
frontmatter fields blank until they are populated. An empty list
(`tags: []`) is a real list value, not null, and is validated as a list.

### Duplicate YAML Keys

Before validation, the frontmatter is re-parsed with `safe_load_yaml`
to detect duplicate keys. If a duplicate is found, a single
`duplicate_key` error is returned and validation stops (the data is
unreliable).

### Type Checking

The validator compares YAML-parsed Python types against the declared
schema type. No type coercion is performed. Two subclass guards are
applied:

- `bool` values are rejected for `int` fields (Python's `bool` is a
  subclass of `int`).
- `datetime.datetime` values are rejected for `date` fields (Python's
  `datetime` is a subclass of `date`). YAML parses timestamps like
  `2026-03-04T12:00:00` as `datetime.datetime`, not `datetime.date`.

Both guards also apply to `allowed` value validation in the schema
loader.

### Error Short-Circuiting

When a field has the wrong type, subsequent checks (allowed values,
list item checks) are skipped for that field. This prevents cascading
errors from a single root cause.

## Error Types

| Rule ID                                   | Trigger                          |
|-------------------------------------------|----------------------------------|
| `schema.frontmatter.missing_field`        | Required field not present       |
| `schema.frontmatter.extra_field`          | Field not defined in schema      |
| `schema.frontmatter.wrong_type`           | Value type does not match schema, or frontmatter is not a mapping |
| `schema.frontmatter.value_not_allowed`    | Value not in `allowed` list      |
| `schema.frontmatter.duplicate_list_item`  | List contains duplicate entries  |
| `schema.frontmatter.map_not_supported`    | Field value is a YAML map        |
| `schema.frontmatter.duplicate_key`        | YAML key appears more than once  |
| `schema.frontmatter.list_item_not_string` | List item is not a string        |

## CLI Integration

The `--frontmatter-schema` flag in `tiredize/cli.py` passes the schema
file path to `_run_frontmatter_schema()`, which calls
`load_frontmatter_schema()` and `validate()`. Error handling catches
`ValueError`, `FileNotFoundError`, and `yaml.YAMLError`, printing to
stderr and returning exit code 1.

## Design Decisions

- **Duplicate keys are caught while parsing,** with a `SafeLoader`
  subclass, because `yaml.safe_load` silently keeps the last value and
  the earlier one is lost. It is used only for schema loading and
  frontmatter validation.
- **A YAML null is "not provided",** always rather than through a
  per-field flag, so optional fields can be left blank (`assignee:`)
  until filled.
- **`int` rejects `bool`,** matching the linter's `get_config_int()`.

- **Explicit types over inferred.** The schema declares expected types
  explicitly rather than inferring from YAML parsing. Makes schemas
  self-documenting.
- **No type coercion.** Validates YAML's native parsed types as-is.
- **`allowed` as a constraint, not a type.** Enum-like validation via
  `allowed` on any field type.
- **List items always strings.** Covers all current use cases. Can be
  extended with `items_type` later.
- **Duplicate list items always rejected.** No opt-out flag.
- **No nesting support.** Map values produce a clear error.
  `type: map` can be added later.
- **Required by default.** Safer for community-submission validation.
- **Colocated loader and validator.** Flat data model does not warrant
  separate modules.
