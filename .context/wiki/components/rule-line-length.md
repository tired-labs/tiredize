# Rule: line_length

## Overview

The `line_length` linter rule (`tiredize/linter/rules/line_length.py`). Reports lines longer than a configured maximum. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key              | Type   | Required | When absent     | Accepted values          |
|------------------|--------|----------|-----------------|--------------------------|
| `maximum_length` | `int`  | yes      | —               | Any integer; no bound is checked |
| `exclude`        | `list` | no       | no exemptions   | Element vocabulary names |

## Behaviour

Reports a line longer than `maximum_length` characters, counted in
Unicode code points with the line ending removed. The finding covers
the overflow, from `maximum_length` to the end of the line. A line that
overlaps any element named in `exclude`, even partly, is exempt as a
whole. A non-string entry or an unknown name in `exclude` raises
`ValueError`.

## Design Decisions

- **`maximum_length` is required,** because the rule measures nothing without it; `exclude` has a working default of no exemptions.
