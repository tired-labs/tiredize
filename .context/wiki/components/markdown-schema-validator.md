# Markdown Schema Validator

## Overview

The markdown schema validator checks a document's section structure
against a user-defined YAML schema. It owns structural validation:
sections exist, are in the correct order, at the correct heading level,
and satisfy repeat bounds. Content validation within sections belongs
in the [linter](./linter-engine.md), not here (see
[scope](../overview/scope.md)). It reads the sections the [markdown
parser](./markdown-parser.md) builds. The schema loader lives in
`tiredize/markdown/types/schema.py` and the validator in
`tiredize/validators/markdown_schema.py`.

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
unordered mode based on `schema.enforce_order`; the chosen mode applies
at every nesting level. Returns a list of `RuleResult` instances with
rule IDs from the table below. Raises `AmbiguityError` (see Exceptions).

### Schema Loader

```python
# tiredize/markdown/types/schema.py
def load_schema(yaml_string: str) -> SchemaConfig:
```

Parses a YAML string with `yaml.safe_load` into a `SchemaConfig`.
Validates the schema itself before returning: unknown keys at the top
level, in a section or in `repeat`, value types, name/pattern mutual
exclusivity, child level consistency, repeat bound types (must be int),
repeat bound values (must not be negative, max must not be less than
min), and regex pattern syntax (compiled at load time via
`re.compile()`). Schema faults raise `ValueError` with the messages
listed under Loader Errors. Malformed YAML raises `yaml.YAMLError`. An
unknown key that YAML reads as a non-string (for example `1: x`, at the
top level or in a section) raises `TypeError` while the error message
is being built. How the CLI handles each exception is described on the
[CLI](./cli.md) page.

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

An entry is repeating when `repeat_min` is not `None`; `repeat_max` is
only consulted on a repeating entry.

### Exceptions

```python
# tiredize/validators/markdown_schema.py
class AmbiguityError(Exception):
```

Raised when a document section matches more than one sibling schema
entry (e.g., a catch-all pattern alongside a specific name). The
message is `Section '<title>' matches multiple schema entries: <list>`,
where `<list>` names every matching entry in schema order as
`name='<name>'` or `pattern='<pattern>'`, comma-separated. Validation
stops at the first ambiguous section reached and no findings are
returned.

The check runs for each group of sibling sections the validator
descends into, against that group's schema entries. Sections under an
unexpected section, or under a second or later duplicate in unordered
mode, are never examined, so ambiguity there is not detected.

### Error Types

| Rule ID                                | Message format | Position | Fires when |
|----------------------------------------|----------------|----------|------------|
| `schema.markdown.missing_section`      | `Missing required section: '<name or pattern>'` | offset 0, length 0 | A required non-repeating entry has no matching section |
| `schema.markdown.unexpected_section`   | `Unexpected section '<title>'` | the section's heading | A section no entry accepts, and `allow_extra_sections` is false (see the algorithms for which sections count) |
| `schema.markdown.wrong_level`          | `Section '<title>' is level <n>, expected <m>` | the section's heading | A matched section's heading level differs from the entry's `level` |
| `schema.markdown.out_of_order`         | `Section '<title>' is out of order` | the section's heading | Ordered mode: a section matches a deferred required entry |
| `schema.markdown.repeat_below_minimum` | `Section matching '<name or pattern>' appears <count> time(s), minimum is <min>` | offset 0, length 0 | A repeating entry matched fewer than `min` sections |
| `schema.markdown.repeat_above_maximum` | `Section matching '<name or pattern>' appears <count> time(s), maximum is <max>` | offset 0, length 0 | A repeating entry matched more than `max` sections |

A heading position runs from the first `#` to the end of the title,
newline excluded. Findings about something absent carry offset 0 and
length 0, so they are reported at line 1, column 0. The level-0 section
of a document with no heading (see Documents Without Headings) has
length 0 and an offset at the start of the markdown body, just after
any frontmatter.

`<name or pattern>` is the entry's `name` if it is non-empty, otherwise
its `pattern`; an entry with `name: ""` therefore renders as `'None'`.

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

The file must be a YAML mapping. An empty file (or one holding only
comments) is a valid schema with no sections, so every top-level
document section is reported as unexpected. Any key not listed below,
at the top level, in a section or in `repeat`, is rejected. Duplicate
keys are not detected: YAML keeps the last value. Every fault in the
schema file is raised before any document is checked.

A key given an empty (YAML `null`) value counts as absent for `name`,
`pattern` and `repeat`, and is rejected for every other key.

### Top-Level Keys

| Key                    | Type   | Required | When absent | Accepted values |
|------------------------|--------|----------|-------------|-----------------|
| `sections`             | list   | no       | no sections | Section definitions (below) |
| `enforce_order`        | bool   | no       | `true`      | `true` checks sibling order; `false` checks presence only, at every nesting level |
| `allow_extra_sections` | bool   | no       | `false`     | `true` accepts document sections the schema does not define, at every nesting level |

### Section Definition Keys

| Key        | Type   | Required | When absent            | Accepted values |
|------------|--------|----------|------------------------|-----------------|
| `name`     | string | one of `name` or `pattern` | —    | Exact, case-sensitive header title. An empty string is accepted but matches only the title of a document with no headings |
| `pattern`  | string | one of `name` or `pattern` | —    | Python `re` regular expression, matched against the whole title (`re.fullmatch`); must compile |
| `level`    | int    | no       | parent's level + 1 (1 at the top) | 1 to 6, greater than the parent's level; may skip levels; `bool` is rejected |
| `required` | bool   | no       | `true`                 | `false` lets the section be absent; ignored on a repeating entry |
| `repeat`   | `true` or mapping | no | the section appears at most once | `true` (one or more, no upper bound) or a mapping with `min` and `max`; `false` and other values are rejected |
| `sections` | list   | no       | no children: any subsection is unexpected | Section definitions |

### `repeat` Mapping Keys

| Key   | Type | Required | When absent | Accepted values |
|-------|------|----------|-------------|-----------------|
| `min` | int  | no       | `1`         | 0 or more; `0` makes the repeating entry optional; `bool` is rejected |
| `max` | int  | no       | no limit    | 0 or more, and not less than `min`; `bool` is rejected |

`repeat: {}` therefore means one or more. `max: 0` is only valid with
`min: 0`, and then any matching section reports
`repeat_above_maximum`. An explicit `min: null` leaves the entry
non-repeating: `max` is stored but has no effect.

### Loader Errors

Every message below is raised as `ValueError`. `<type>` is the Python
type name of the offending value (`NoneType` for an empty value).

| Fault | Message |
|-------|---------|
| File is not a mapping | `Schema must be a YAML mapping, got <type>.` |
| Unknown top-level key | `Unknown top-level key(s): <keys>.` (sorted, comma-separated) |
| `sections` not a list (top level or in a section) | `'sections' must be a list.` |
| `allow_extra_sections` or `enforce_order` not a bool | `'<key>' must be a bool, got <type>.` |
| Section not a mapping | `Each section must be a YAML mapping, got <type>.` |
| Unknown section key | `Unknown section key(s): <keys>.` |
| `name` or `pattern` not a string | `'<key>' must be a string, got <type>.` |
| Both `name` and `pattern` | `Section must have 'name' or 'pattern', not both.` |
| Neither `name` nor `pattern` | `Section must have either 'name' or 'pattern'.` |
| Pattern does not compile | `Invalid regex pattern '<pattern>': <re error>` |
| `level` not an int | `'level' must be an integer, got <type>.` |
| `level` outside 1 to 6 | `Section level <n> must be between 1 and 6.` |
| `level` not above the parent's | `Section level <n> must be greater than parent level <p>.` |
| `repeat` not `true`, null or a mapping | `'repeat' must be true or a mapping with min/max bounds (e.g., repeat: {min: 1, max: 3}), got <type>: <repr>.` |
| Unknown `repeat` key | `Unknown repeat key(s): <keys>.` |
| `min` or `max` not an int | `repeat.min must be an integer.` / `repeat.max must be an integer.` |
| `min` or `max` negative | `repeat.min must not be negative.` / `repeat.max must not be negative.` |
| `max` below `min` | `repeat.max (<max>) must not be less than repeat.min (<min>).` |
| `required` not a bool | `'required' must be a bool, got <type>.` |

### Constraints

- Each section definition has exactly one of `name` or `pattern`.
- On a repeating entry, `repeat` alone decides whether it may be absent:
  `required` has no effect there. `repeat: true` with `required: false`
  still reports `repeat_below_minimum` when no section matches; only
  `min: 0` makes a repeating entry optional.
- `sections` nests child definitions under this one. Children are
  checked only within the document section their parent matched, so
  nesting in the schema mirrors nesting in the document.
- A document section that matches more than one sibling definition
  raises `AmbiguityError` (see Exceptions).

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

Validation starts from the document's root sections: those that are
not a subsection of another section. Each group of sibling sections is
validated against the matching group of schema entries, and every
matched section's subsections are validated against that entry's
`sections`, recursively.

### Matching Rules

- `name`: case-sensitive exact match against the section header title.
  The title is everything after the `#` run and its whitespace, so
  trailing spaces or closing `#` characters are part of it.
- `pattern`: full-match regex against the section header title.
- `level` plays no part in matching. A section matched at a different
  heading level reports `wrong_level` and is otherwise validated
  normally, children included.

### Ordered Mode (`enforce_order: true`)

Ordering is enforced among sibling sections under the same parent, not
across nesting levels. The validator walks the document sections in
order with a pointer into the schema entries. It also keeps a list of
deferred entries: required entries it skipped over. An entry is
required when it is non-repeating with `required: true`, or repeating
with `min` greater than 0. For each document section:

1. If the section matches a deferred entry, that entry leaves the
   deferred list and the section reports `out_of_order`. A repeating
   entry then consumes the run of consecutive matching sections (see
   below); a non-repeating one validates the section's children. The
   heading level of a non-repeating section matched this way is not
   checked.
2. Otherwise, if the schema pointer is past the last entry, the section
   reports `unexpected_section`.
3. Otherwise, if the section matches the entry at the pointer, it is
   validated against it (level and children), and the pointer advances
   to the next entry.
4. Otherwise, if the section matches a later entry, every entry between
   the pointer and that entry is skipped and the pointer moves to the
   match, which is then tried as in step 3. Skipped required entries are
   deferred. Skipped optional entries (`required: false`, or repeating
   with `min: 0`) are dropped: if their section appears later in the
   document it reports `unexpected_section`, not `out_of_order`.
5. Otherwise the section matches nothing at or after the pointer and is
   not deferred, so it reports `unexpected_section`. This includes a
   second occurrence of a non-repeating section and a repeating section
   that is not contiguous with its run.

After the last document section, each entry still deferred reports
`missing_section`, or `repeat_below_minimum` with a count of 0 if it is
repeating. Then each entry from the pointer onwards that is required
reports the same; optional entries are silently accepted.

For example, with entries A, B, C (all required): document B, C, A
reports `out_of_order` on A; document C, A, B reports `out_of_order` on
both A and B, because C was matched first and A and B were deferred.

A repeating entry consumes the run of consecutive document sections
that match it, checking every occurrence's heading level and validating
each occurrence's children independently. The run's length is then
checked against `min` and `max`. Only a contiguous run counts; later
occurrences fall under step 5.

`unexpected_section` is reported on the heading alone: the section's
subsections are not examined at all. Findings follow the walk, so a
section's child findings come before its later siblings' findings, and
end-of-walk `missing_section` and repeat-count findings come after the
group's section findings.

### Unordered Mode (`enforce_order: false`)

Each schema entry is checked in schema order against all sibling
document sections:

1. A repeating entry takes every matching section. Each one is
   level-checked and its children validated; the count is then checked
   against `min` and `max`.
2. A non-repeating entry with no match reports `missing_section` if it
   is required.
3. A non-repeating entry with matches takes the first one, level-checks
   it and validates its children. Each further match reports
   `unexpected_section` unless `allow_extra_sections` is true; its
   children are not examined.

After all entries, if `allow_extra_sections` is false, every section
no entry took reports `unexpected_section`, in document order. Children
are validated in unordered mode as well.

### Documents Without Headings

A document with no heading at all, including an empty document, is one
section with level 0 and an empty title (see [markdown
parser](./markdown-parser.md)). It is validated like any root section:
unless `allow_extra_sections` is true it reports `Unexpected section ''`,
and a pattern that matches the empty string (such as `.*`) matches it
and reports `Section '' is level 0, expected 1`. Text before the first
heading of a document that has headings belongs to no section and is
not validated.

### Empty Schema Sections

When a schema entry defines no children and the document has children
under the matched section, those children are flagged as
`unexpected_section` (unless `allow_extra_sections` is true).

## Design Decisions

- **Schema validates structure, linter validates content.** See
  [scope](../overview/scope.md).
- **An entry with no `sections` forbids subsections.** Treating empty
  children as "anything goes" let any subsection through silently.
- **A skipped required entry is deferred,** so a later occurrence
  reports `out_of_order` rather than an immediate `missing_section` or
  `repeat_below_minimum`, and every occurrence of a repeating section
  has its level checked.

- **Schema self-validation at load time.** The loader validates the
  schema file itself before running document validation: name/pattern
  mutual exclusivity, child level consistency, repeat bound types and
  values, and regex pattern syntax. Invalid schemas raise `ValueError`
  with descriptive messages rather than producing confusing validation
  results.

- **Ambiguity detection.** Both ordered and unordered modes raise
  `AmbiguityError` when a document section matches multiple sibling
  schema entries, preventing nondeterministic results.
