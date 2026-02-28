# Specification: Linter

## Overview

The linter engine discovers, selects, and runs pluggable rule modules
against parsed documents. It owns rule discovery, rule configuration,
and result normalization. Located in `tiredize/linter/`.

## Contracts and Interfaces

### Engine Entry Point

```python
# tiredize/linter/engine.py
def run_linter(
    document: Document,
    rule_configs: dict[str, dict[str, Any]] | None = None
) -> list[RuleResult]:
```

Discovers all available rules via `discover_rules()`, selects the
enabled subset based on `rule_configs`, runs each rule's `validate`
function, and normalizes results by injecting the `rule_id`. Returns
the aggregated list.

### Rule Discovery

```python
# tiredize/linter/rules/__init__.py
RuleFunc = Callable[[Document, dict[str, Any]], list[RuleResult]]

@dataclass(frozen=True)
class Rule:
    id: str
    func: RuleFunc
    description: str | None = None

def discover_rules(
    package: str | None = None
) -> dict[str, Rule]:
```

Discovers rules by iterating all non-private modules in a package
(default: `tiredize.linter.rules`) via `pkgutil.iter_modules()`. A
valid rule module must expose a function named `validate`. The rule ID
is derived from the module filename (e.g., `line_length.py` produces
`line_length`). The description is extracted from the function's
docstring via `inspect.getdoc()`.

Raises `RuleNotFoundError` (defined in `tiredize/core_types.py`) when
a requested rule ID does not match any discovered rule.

### Rule Module Convention

Each rule is a Python module under `tiredize/linter/rules/`. A valid
rule module must:

1. Be a non-private module (filename must not start with `_`).
2. Expose a `validate(document: Document, config: dict[str, Any]) -> list[RuleResult]` function.
3. Return `RuleResult` instances with `rule_id=None` (the engine fills
   this in from the module name).

Users can add custom rules by placing modules in a package that follows
this convention and passing the package name to `discover_rules()`.

### Configuration Helpers

```python
# tiredize/linter/utils.py
def get_config_int(config: dict[str, Any], key: str) -> int | None
def get_config_str(config: dict[str, Any], key: str) -> str | None
def get_config_bool(config: dict[str, Any], key: str) -> bool | None
def get_config_dict(
    config: dict[str, Any], key: str
) -> dict[str, Any] | None
def get_config_list(
    config: dict[str, Any], key: str
) -> list[str] | None
```

Type-safe retrievals from rule config dictionaries. All return `None`
if the key is missing or the value is the wrong type. No exceptions
raised on type mismatch.

### URL Validation

```python
# tiredize/linter/utils.py
def check_url_valid(
    document: Document,
    url: str,
    timeout: float | None = None,
    headers: dict[str, Any] | None = None,
    allow_redirects: bool | None = None,
    verify_ssl: bool | None = None
) -> tuple[bool, int | None, str | None]:
```

Returns `(is_valid, status_code, error_message)`. Never raises
exceptions; all failures are returned in the tuple. Handles three URL
types:

- `#anchor` -- checks against `document.sections[*].header.slug`.
- `./relative` -- resolves relative to `document.path` and checks
  file existence.
- `http(s)://` -- makes an HTTP request with the given options.

## File Layout

```
tiredize/linter/
├── __init__.py
├── engine.py         run_linter, _select_rules
├── utils.py          get_config_*, check_url_valid
└── rules/
    ├── __init__.py   Rule, RuleFunc, discover_rules
    ├── line_length.py
    ├── links.py
    ├── tabs.py
    └── trailing_whitespace.py
```

## Design Decisions

None recorded yet.
