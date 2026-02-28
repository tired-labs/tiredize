# Specification: Markdown Schema Validator

## Overview

The markdown schema validator checks a document's section structure
against a user-defined YAML schema. It owns structural validation:
sections exist, are in the correct order, at the correct heading level,
and satisfy repeat bounds. Content validation within sections belongs
in linter rules, not here. Located in `tiredize/validators/`.

## Contracts and Interfaces

### Public API

```python
# tiredize/validators/markdown_schema.py
def validate(
    document: Document,
    schema: SchemaConfig,
) -> list[RuleResult]:
```

Validates the document against the schema. Dispatches to ordered or
unordered mode based on `schema.enforce_order`. Returns a list of
`RuleResult` instances with rule IDs from the table below.

### Schema Loader

```python
# tiredize/markdown/types/schema.py
def load_schema(yaml_string: str) -> SchemaConfig:
```

Parses a YAML string into a `SchemaConfig`. Validates the schema
itself before returning: name/pattern mutual exclusivity, child level
consistency, repeat bound types (must be int), repeat bound values
(must not be negative, max must not be less than min), and regex
pattern syntax (compiled at load time via `re.compile()`). Raises
`ValueError` for all validation failures.

### Data Model

```python
# tiredize/markdown/types/schema.py
@dataclass(frozen=True)
class SchemaSection:
    level: int = 1
    name: str | None = None
    pattern: str | None = None
    repeat_max: int | None = None
    repeat_min: int | None = None
    required: bool = True
    sections: list[SchemaSection] = field(default_factory=list)

@dataclass(frozen=True)
class SchemaConfig:
    allow_extra_sections: bool = False
    enforce_order: bool = True
    sections: list[SchemaSection] = field(default_factory=list)
```

### Exceptions

```python
# tiredize/validators/markdown_schema.py
class AmbiguityError(Exception):
```

Raised when a document section matches multiple sibling schema entries
(e.g., a catch-all pattern alongside a specific name). Fails fast
before any validation logic runs.

### Error Types

| Rule ID                                | Trigger                        |
|----------------------------------------|--------------------------------|
| `schema.markdown.missing_section`      | Required section not found     |
| `schema.markdown.unexpected_section`   | Section not defined in schema  |
| `schema.markdown.wrong_level`          | Heading level mismatch         |
| `schema.markdown.out_of_order`         | Section in wrong position      |
| `schema.markdown.repeat_below_minimum` | Fewer occurrences than min     |
| `schema.markdown.repeat_above_maximum` | More occurrences than max      |

## File Layout

```
tiredize/markdown/types/
└── schema.py          SchemaConfig, SchemaSection, load_schema

tiredize/validators/
└── markdown_schema.py validate, AmbiguityError, ordered/unordered
                       validation internals
```

## Schema File Format

The schema is a YAML file passed to the CLI via `--markdown-schema`.

### Top-Level Properties

| Property               | Type | Default | Description                    |
|------------------------|------|---------|--------------------------------|
| `enforce_order`        | bool | `true`  | Validate section ordering      |
| `allow_extra_sections` | bool | `false` | Allow sections not in schema   |
| `sections`             | list | --      | Ordered list of section defs   |

### Section Definition Properties

| Property   | Type        | Default        | Description                     |
|------------|-------------|----------------|---------------------------------|
| `name`     | string      | --             | Exact section header match      |
| `pattern`  | string      | --             | Regex pattern for header match  |
| `level`    | int         | parent + 1     | Required heading level (1-6, must be greater than parent level) |
| `required` | bool        | `true`         | Section must be present         |
| `repeat`   | bool or map | --             | Section may appear repeatedly   |
| `sections` | list        | --             | Nested child section defs       |

### Constraints

- Exactly one of `name` or `pattern` must be present. Both or neither
  is an error.
- `level` is optional. When omitted, it is inferred as the parent
  section's level + 1. Top-level sections with no parent default to 1.
  When present, the loader validates it is between 1 and 6 and
  strictly greater than the parent level. Explicit levels may skip
  levels (e.g., parent level 1, child level 3 is valid).
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
        sections:
          - pattern: ".+"
            level: 3
            required: false
            repeat:
              min: 0
            sections:
              - pattern: ".+"
                level: 4
                required: false
                repeat:
                  min: 0
                sections:
                  - pattern: ".+"
                    level: 5
                    required: false
                    repeat:
                      min: 0
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
2. If the current document section matches a later schema entry and
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

Nested repeat groups: children of a repeating section are defined via
the `sections` field on that entry. Each instance of the parent must
independently satisfy all child section requirements.

When the ordered validator skips past a repeating schema entry to match
a later entry, the repeating entry is deferred. If it appears later in
the document, it reports `out_of_order`. If it never appears, it
reports `repeat_below_minimum` at end of validation.

Every occurrence of a repeating section validates heading level (not
just the first occurrence).

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

### Empty Schema Sections

When a schema entry defines no children and the document has children
under the matched section, those children are flagged as
`unexpected_section` (unless `allow_extra_sections` is true).

## Design Decisions

- **Schema validates structure, linter validates content.** The schema
  engine checks that sections exist, are in the right order, at the
  right heading level. Anything about what is inside a section (table
  contents, link formats, required fields) belongs in a linter rule.

- **Schema self-validation at load time.** The loader validates the
  schema file itself before running document validation: name/pattern
  mutual exclusivity, child level consistency, repeat bound types and
  values, and regex pattern syntax. Invalid schemas raise `ValueError`
  with descriptive messages rather than producing confusing validation
  results.

- **Ambiguity detection.** Both ordered and unordered modes raise
  `AmbiguityError` when a document section matches multiple sibling
  schema entries. This fails fast before validation logic runs,
  preventing nondeterministic results.
