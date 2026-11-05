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
`allowed` value type consistency, and unknown property rejection. Schema
faults raise `ValueError` with the messages listed under Loader Errors.
Malformed YAML raises `yaml.YAMLError`. An unknown top-level key that
YAML reads as a non-string (for example `1: x`) raises `TypeError`
while the error message is being built.

### Duplicate Key Loader

```python
# tiredize/validators/frontmatter_schema.py
def safe_load_yaml(text: str):
```

Parses YAML with duplicate key detection, at any nesting depth. Uses a
`SafeLoader` subclass with a custom constructor for
`DEFAULT_MAPPING_TAG` that calls `construct_pairs` to detect duplicates
before building the dict. Raises `ValueError` with
`Frontmatter contains duplicate key: '<key>'` when a mapping key
appears more than once, and with `Mapping key <repr> is unhashable
(<type>)` when a key is a sequence or mapping (the repr shows the key
before its contents are built, e.g. `[]`). Keys are compared after YAML
typing with Python equality, so `1`, `1.0` and `true` count as the same
key. Any other YAML fault raises `yaml.YAMLError`. Used in both the
schema loader and the frontmatter validation path.

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
twice (see Duplicate Key Loader). Every fault in the schema file is
raised before any document is checked; the [CLI](./cli.md) page
describes how each is reported. An empty file is rejected, because
`fields` is required.

A key given an empty (YAML `null`) value is rejected, except `allowed`,
where `null` means no restriction.

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
| `allowed`  | list   | no       | any value of the type | A non-empty list. Entries must have the field's type (strings for a `list` field), with the same guards as values: no `bool` for `int`, no `int` for `float`, no timestamp for `date`. `null` is the same as absent |

### Loader Errors

Every message below is raised as `ValueError`. `<type>` is the Python
type name of the offending value (`NoneType` for an empty value).

| Fault | Message |
|-------|---------|
| Duplicate key | `Schema contains duplicate key: Frontmatter contains duplicate key: '<key>'` |
| Unhashable key | `Schema contains duplicate key: Mapping key <repr> is unhashable (<type>)` |
| File is not a mapping | `Schema must be a YAML mapping, got <type>.` |
| Unknown top-level key | `Unknown top-level key(s): <keys>.` (sorted, comma-separated) |
| No `fields` key | `Schema must contain a 'fields' key.` |
| `fields` not a mapping | `'fields' must be a YAML mapping, got <type>.` |
| `allow_extra_fields` not a bool | `'allow_extra_fields' must be a bool, got <type>.` |
| Field name not a string | `Field name must be a string, got <type>: <repr>. Quote it in YAML to prevent type coercion.` |
| Field definition not a mapping | `Field '<name>' definition must be a YAML mapping, got <type>.` |
| Unknown field property | `Unknown property in field '<name>': <keys>.` |
| No `type` | `Field '<name>' must declare a 'type'.` |
| Unknown `type` | `Field '<name>' has unknown type '<value>'. Valid types: bool, date, float, int, list, string.` |
| `required` not a bool | `'required' for field '<name>' must be a bool, got <type>.` |
| `allowed` not a list | `'allowed' for field '<name>' must be a list, got <type>.` |
| `allowed` empty | `'allowed' for field '<name>' must not be empty.` |
| `allowed` entry of the wrong type | `'allowed' value <repr> for field '<name>' has wrong type (<type>, expected <field type>).` |
| `allowed` entry not a string on a `list` field | `'allowed' values for list field '<name>' must be strings, got <type>: <repr>.` |

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
  rejected. If any item is not a string, each such item reports
  `list_item_not_string` and the field's duplicate and `allowed` checks
  are skipped. Otherwise each repeated occurrence of an item reports
  `duplicate_list_item` (three `a` items give two findings), and each
  occurrence of a disallowed item reports `value_not_allowed`,
  duplicates included. An empty list passes, even with `allowed`.
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

Every finding points at the whole frontmatter block, from the opening
`---` through the closing `---` and its newline, or at offset 0 with
length 0 when there is none.

### Empty Field Values

A field that is present but has an empty (YAML `null`) value — for
example a bare `assignee:` line — is treated as **not provided**. A
required field with a null value reports `missing_field`; an optional
(`required: false`) field with a null value passes with no error and is
not type-checked. This supports the convention of leaving optional
frontmatter fields blank until they are populated. An empty list
(`tags: []`) is a real list value, not null, and is validated as a list.
This applies only to fields the schema defines: an undefined key with
an empty value still reports `extra_field` when extra fields are not
allowed.

### Duplicate YAML Keys

Before validation, the frontmatter is re-parsed with `safe_load_yaml`
to detect duplicate keys. If a duplicate is found, a single
`duplicate_key` error is returned, for the first duplicate found, and
validation stops (the data is unreliable). Because keys are compared
with Python equality, distinct keys such as `1` and `true` also trigger
it.

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

### Finding Order

Findings come in this order: `wrong_type` for frontmatter that is not a
mapping; every `missing_field`, in schema order; every `extra_field`, in
frontmatter order; then each defined field's value findings, in schema
order.

## Error Types

Every finding's position is the frontmatter block (see Missing
Frontmatter). In the messages, `<value>` and `<item>` use Python's
`str()`, and `<allowed>` is the Python repr of the `allowed` list (for
example `[datetime.date(2024, 1, 1)]`).

| Rule ID                                   | Message format | Fires when |
|-------------------------------------------|----------------|------------|
| `schema.frontmatter.missing_field`        | `Missing required field: '<name>'` | A required field is absent or null |
| `schema.frontmatter.extra_field`          | `Unexpected field: '<key>'` | A key is not defined in the schema and `allow_extra_fields` is false |
| `schema.frontmatter.wrong_type`           | `Field '<name>' has wrong type: expected <type>, got <python type>` | A value's type does not match the schema |
| `schema.frontmatter.wrong_type`           | `Frontmatter must be a YAML mapping, got <python type>` | The frontmatter is not a mapping |
| `schema.frontmatter.value_not_allowed`    | `Field '<name>' value '<value>' is not allowed. Accepted values: <allowed>` | A scalar value is not in `allowed` |
| `schema.frontmatter.value_not_allowed`    | `List field '<name>' contains disallowed item: '<item>'. Accepted values: <allowed>` | A list item is not in `allowed` |
| `schema.frontmatter.duplicate_list_item`  | `List field '<name>' contains duplicate item: '<item>'` | A list item repeats |
| `schema.frontmatter.map_not_supported`    | `Field '<name>' is a map — maps are not supported` | A defined field's value is a YAML mapping, whatever its type |
| `schema.frontmatter.duplicate_key`        | The `safe_load_yaml` message, e.g. `Frontmatter contains duplicate key: '<key>'` | A key repeats in any mapping of the frontmatter |
| `schema.frontmatter.list_item_not_string` | `List field '<name>' contains non-string item: <repr> (<python type>)` | A list item is not a string |

## CLI Integration

The `--frontmatter-schema` flag passes the schema file to
`load_frontmatter_schema()` and `validate()`; the [CLI](./cli.md) page
describes how their exceptions and findings are reported.

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
