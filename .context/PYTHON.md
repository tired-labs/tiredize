# Python Conventions

Language-specific conventions for Python projects. These apply to any Python
project that references this file. Conventions follow PEP 8 unless explicitly
overridden.

## Language and Runtime

- Python >= 3.10
- Build system: Hatchling (`pyproject.toml`)

## Linting

Flake8 is the project linter. Unless a configuration file is present, default
settings apply. Run it against both source and test directories:

```
flake8 <source_package> tests
```

All code must pass flake8 before it is presented for review.

## Testing

Tests use pytest. Run the full suite with:

```
pytest
```

All tests must pass before presenting changes for review. If a test fails,
report what failed and why before showing the change.

Tests mirror the source layout. A test file for `<package>/foo/bar.py`
belongs at `tests/foo/test_bar.py`.

Every `tests/` subdirectory must contain an `__init__.py` file.

## Line Length

Per PEP 8:

- Code lines: 79 characters maximum
- Docstrings and comments: 72 characters maximum

## Type Annotations

Use modern Python built-in generics and union syntax. Do not import `List`,
`Dict`, `Optional`, `Tuple`, or `Union` from `typing`.

```python
# Correct
def example(items: list[str], config: dict[str, Any]) -> str | None:

# Incorrect
def example(items: List[str], config: Dict[str, Any]) -> Optional[str]:
```

Import from `typing` only for names that have no builtin equivalent, such as
`Any`, `Callable`, `ClassVar`, and `TypeVar`.

Include `from __future__ import annotations` at the top of every module.

Note: existing code in a project may not be fully migrated to this convention.
Do not refactor existing code to match unless you are already modifying that
code for another reason or the user explicitly requests a migration.

## Naming

Per PEP 8:

- Modules and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private attributes and methods: `_single_leading_underscore`
- Name-mangled attributes: `__double_leading_underscore`
- Throwaway variables: `_`

## Imports

Per PEP 8, use one import per line. Prefer `from` imports for specific names.
Group imports in this order with a blank line between each group:

1. Standard library
2. Third-party packages
3. Local project imports

```python
# Standard library
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

# Third-party
import yaml

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
```

## Dataclasses

Prefer dataclasses for data types. Value types that should not be mutated use
`frozen=True`. Types that are built up incrementally use `frozen=False`.
