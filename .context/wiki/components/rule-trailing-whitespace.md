# Rule: trailing_whitespace

## Overview

The `trailing_whitespace` linter rule (`tiredize/linter/rules/trailing_whitespace.py`). Reports whitespace at the end of a line. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key       | Type   | Required | When absent                   | Accepted values |
|-----------|--------|----------|-------------------------------|-----------------|
| `allowed` | `bool` | no       | trailing whitespace forbidden | `true` permits it, which makes the rule check nothing |

## Behaviour

Reports whitespace (any character `str.isspace()` accepts) before the
line ending, one finding per line covering the whole run.

## Design Decisions

- **`allowed` is optional,** because with the key absent the rule still forbids its target, so enabling it is never a no-op (see [linter engine](./linter-engine.md)).

## Open Questions

- `allowed: true` leaves the enabled rule checking nothing, which the "never a no-op" principle forbids for an omitted key but not for this value.
