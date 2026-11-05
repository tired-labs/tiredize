# Rule: elements

## Overview

The `elements` linter rule (`tiredize/linter/rules/elements.py`). Reports each occurrence of an element type the configuration disallows. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key        | Type   | Required | When absent | Accepted values                              |
|------------|--------|----------|-------------|----------------------------------------------|
| `disallow` | `list` | yes      | —           | Element vocabulary names; `[]` allows everything |

Entries are checked before the document is read, so a bad entry raises
even when the document holds no elements. `disallow: []` returns before
any check.

| Entry            | Error                                                               |
|------------------|---------------------------------------------------------------------|
| Not a string     | `ValueError: disallow entries must be strings, got 'NoneType': None` (type name and `repr` of the entry) |
| Unknown name     | `ValueError: Unknown element name in disallow: 'headers'`           |

## Behaviour

Reports each occurrence of a disallowed element type. Elements with an
empty span are skipped. A name listed twice reports each of its
elements twice.

The rule sees only the elements the [markdown
parser](./markdown-parser.md) extracts. In a document with headings,
elements before the first heading are not reported. After frontmatter,
the parser skips one character, so an element starting on the line
right after the frontmatter can be missed.

### Findings

| Rule id    | Message                  | Position                  |
|------------|--------------------------|---------------------------|
| `elements` | `<Label> is not allowed.` (for example `Header is not allowed.`); labels are in the engine's element vocabulary | The element's full span |

Findings are ordered by section, then by the order of names in
`disallow`, then by the parser's order for that element type; they are
not sorted by position.

## Design Decisions

- **`disallow` is required,** because the rule inspects nothing without it; an empty list is a deliberate "allow everything".
