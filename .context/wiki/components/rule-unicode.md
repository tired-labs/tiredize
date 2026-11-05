# Rule: unicode

## Overview

The `unicode` linter rule (`tiredize/linter/rules/unicode.py`). Reports non-ASCII characters where the configuration does not permit them. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key       | Type   | Required | When absent   | Accepted values          |
|-----------|--------|----------|---------------|--------------------------|
| `allowed` | `bool` | yes      | —             | `true` or `false`; selects the mode |
| `exclude` | `list` | no       | no exemptions | Element vocabulary names |

`exclude` entries are checked before the document is read, so a bad
entry raises even when the document holds no such element.

| Entry            | Error                                                              |
|------------------|--------------------------------------------------------------------|
| Not a string     | `ValueError: exclude entries must be strings, got 'NoneType': None` (type name and `repr` of the entry) |
| Unknown name     | `ValueError: Unknown element name in exclude: 'nope'`              |

## Behaviour

Reports each non-ASCII character (code point above 127) where it is not
permitted. With `allowed: false`, non-ASCII is forbidden everywhere
except inside the elements named in `exclude`. With `allowed: true`, it
is permitted everywhere except inside those elements, so `allowed: true`
with no `exclude` checks nothing.

The rule scans `document.string`, the whole file including YAML
frontmatter. The file is read as `utf-8`, not `utf-8-sig`, so a
byte-order mark at the start of the file is reported as U+FEFF.

`exclude` uses the elements the [markdown parser](./markdown-parser.md)
extracts. In a document with headings, nothing before the first heading
is inside an element. After frontmatter the parser skips one character,
so an element starting on the line right after the frontmatter can be
missed and positions there are one character off.

### Findings

| Rule id   | Message                                                        | Position |
|-----------|----------------------------------------------------------------|----------|
| `unicode` | `Unicode character <repr> (U+<hex>) is not permitted here.`    | The character: its code-point offset, length 1 |

`<repr>` is Python's `repr()` of the character, so printable characters
appear as they are and invisible ones are escaped:
`Unicode character 'é' (U+00E9) is not permitted here.` and
`Unicode character '\u200b' (U+200B) is not permitted here.`. `<hex>` is
upper case with at least four digits (`U+1F600`). Findings are in
document order.

## Design Decisions

- **`allowed` is required,** because it selects the mode the rule runs in; without it the rule would inspect nothing (see [linter engine](./linter-engine.md)).
