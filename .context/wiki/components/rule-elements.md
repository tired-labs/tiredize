# Rule: elements

## Overview

The `elements` linter rule (`tiredize/linter/rules/elements.py`). Reports each occurrence of an element type the configuration disallows. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key        | Type   | Required | When absent | Accepted values                              |
|------------|--------|----------|-------------|----------------------------------------------|
| `disallow` | `list` | yes      | —           | Element vocabulary names; `[]` allows everything |

## Behaviour

Reports each occurrence of a disallowed element type as `<Label> is
not allowed.` at the element's position. Elements with an empty span
are skipped. A non-string entry or an unknown name raises `ValueError`.

## Design Decisions

- **`disallow` is required,** because the rule inspects nothing without it; an empty list is a deliberate "allow everything".
