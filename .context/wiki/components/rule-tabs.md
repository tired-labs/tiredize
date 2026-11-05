# Rule: tabs

## Overview

The `tabs` linter rule (`tiredize/linter/rules/tabs.py`). Reports tab characters. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key       | Type   | Required | When absent     | Accepted values |
|-----------|--------|----------|-----------------|-----------------|
| `allowed` | `bool` | no       | tabs forbidden  | `false` behaves as absent; `true` permits tabs, which makes the rule check nothing |

## Behaviour

Reports each tab character (`\t`), one finding per tab. The rule scans
`document.string`, the whole file including YAML frontmatter, code
blocks and inline code; it has no `exclude` option.

### Findings

| Rule id | Message                          | Position                   |
|---------|----------------------------------|----------------------------|
| `tabs`  | `Line contains a tab character.` | The tab: its offset, length 1 |

Findings are in document order.

## Design Decisions

- **`allowed` is optional,** because with the key absent the rule still forbids its target, so enabling it is never a no-op (see [linter engine](./linter-engine.md)).
