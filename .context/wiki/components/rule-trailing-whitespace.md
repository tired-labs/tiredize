# Rule: trailing_whitespace

## Overview

The `trailing_whitespace` linter rule (`tiredize/linter/rules/trailing_whitespace.py`). Reports whitespace at the end of a line. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key       | Type   | Required | When absent                   | Accepted values |
|-----------|--------|----------|-------------------------------|-----------------|
| `allowed` | `bool` | no       | trailing whitespace forbidden | `false` behaves as absent; `true` permits it, which makes the rule check nothing |

## Behaviour

The rule scans `document.string`, the whole file including YAML
frontmatter and code blocks. It splits it with Python's
`str.splitlines()` and removes only a trailing `\n` or `\r\n` from each
line. It then reports the run of whitespace (any character
`str.isspace()` accepts, such as space, tab or no-break space) at the
end of what remains, one finding per line.

Consequences:

- A whitespace-only line is reported as a whole.
- A Markdown hard line break (two or more trailing spaces) is reported.
- In a file with CR-only line endings, every line is reported, because
  the lone `\r` is left on the line and counts as whitespace. The same
  happens at the other separators `splitlines()` accepts (`\v`, `\f`,
  `\x1c`, `\x1d`, `\x1e`, `\x85`, U+2028, U+2029). CRLF files are
  unaffected.

### Findings

| Rule id               | Message                              | Position |
|-----------------------|--------------------------------------|----------|
| `trailing_whitespace` | `Line contains trailing whitespace.` | From the first trailing whitespace character to the end of the line, line ending excluded |

Findings are in line order.

## Design Decisions

- **`allowed` is optional,** because with the key absent the rule still forbids its target, so enabling it is never a no-op (see [linter engine](./linter-engine.md)).
