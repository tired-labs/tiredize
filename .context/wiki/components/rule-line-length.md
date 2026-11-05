# Rule: line_length

## Overview

The `line_length` linter rule (`tiredize/linter/rules/line_length.py`). Reports lines longer than a configured maximum. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key              | Type   | Required | When absent     | Accepted values          |
|------------------|--------|----------|-----------------|--------------------------|
| `maximum_length` | `int`  | yes      | —               | Any whole integer, `0` and negatives included (see Behaviour); a float such as `80.0` is rejected |
| `exclude`        | `list` | no       | no exemptions   | Element vocabulary names |

`exclude` entries are checked before the document is read, so a bad
entry raises even when the document holds no such element.

| Entry            | Error                                                              |
|------------------|--------------------------------------------------------------------|
| Not a string     | `ValueError: exclude entries must be strings, got 'NoneType': None` (type name and `repr` of the entry) |
| Unknown name     | `ValueError: Unknown element name in exclude: 'codeblock'`         |

## Behaviour

The rule scans `document.string`, the whole file including any YAML
frontmatter. It splits it with Python's `str.splitlines()` and measures
each line in Unicode code points, with a trailing `\n` or `\r\n`
removed. `splitlines()` also breaks lines at a lone `\r`, `\v`, `\f`,
`\x1c`, `\x1d`, `\x1e`, `\x85`, U+2028 and U+2029, and those separators
are not removed, so they count towards the length: in a file with CR-only
line endings every line counts one extra character, and a form feed
inside a line splits it in two.

A line longer than `maximum_length` is reported. With `0`, every
non-empty line is reported. With a negative value, every line is
reported, empty lines included, and the finding starts before the line
(at a negative offset on the first line).

A line that overlaps any element named in `exclude`, even partly
(including at its line ending), is exempt as a whole. Exclusion uses the
elements the [markdown parser](./markdown-parser.md) extracts: in a
document with headings, nothing before the first heading can be
exempted, and after frontmatter the parser skips one character, so an
element starting on the line right after the frontmatter can be missed
and positions there are one character off.

### Findings

| Rule id       | Message                                                     | Position |
|---------------|-------------------------------------------------------------|----------|
| `line_length` | `Line exceeds maximum length of <maximum_length> (<length> found).` | Offset `line start + maximum_length`, length `length - maximum_length`: the overflow |

Findings are in line order.

## Design Decisions

- **`maximum_length` is required,** because the rule measures nothing without it; `exclude` has a working default of no exemptions.
