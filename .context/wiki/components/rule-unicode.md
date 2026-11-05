# Rule: unicode

## Overview

The `unicode` linter rule (`tiredize/linter/rules/unicode.py`). Reports non-ASCII characters where the configuration does not permit them. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key       | Type   | Required | When absent   | Accepted values          |
|-----------|--------|----------|---------------|--------------------------|
| `allowed` | `bool` | yes      | —             | `true` or `false`; selects the mode |
| `exclude` | `list` | no       | no exemptions | Element vocabulary names |

## Behaviour

Reports each non-ASCII character (code point above 127) where it is not
permitted. With `allowed: false`, non-ASCII is forbidden everywhere
except inside the elements named in `exclude`. With `allowed: true`, it
is permitted everywhere except inside those elements. The message names
the character and its code point. A non-string entry or an unknown name
in `exclude` raises `ValueError`.

## Design Decisions

- **`allowed` is required,** because it selects the mode the rule runs in; without it the rule would inspect nothing (see [linter engine](./linter-engine.md)).
