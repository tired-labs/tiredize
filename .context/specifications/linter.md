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
4. Declare the configuration keys it accepts and the subset it
   requires, and call `validate_config()` as the first statement of
   `validate()`, before reading any key. See "Rule Configuration
   Validation" below for how to classify a key and what the call
   guarantees.

Requirement 4 is not optional and not a convenience: a rule that skips
it reads a mistyped key as an absent one and silently checks nothing,
which is the failure mode `validate_config()` exists to prevent.

The declaration lives inline in the rule module, as module-level
constants — nothing about a rule's key set reaches the `Rule` dataclass
or the discovery mechanism. The shape every built-in rule uses:

```python
# tiredize/linter/rules/<rule_id>.py
_RULE_ID = "line_length"
_ALLOWED_KEYS = {
    "exclude": "list",
    "maximum_length": "int",
}
_REQUIRED_KEYS = ("maximum_length",)


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)
    ...
```

A rule that accepts no keys at all still calls `validate_config()`,
with an empty `_ALLOWED_KEYS`; the call is what makes any configuration
of that rule an error rather than a silent no-op.

Users can add custom rules by placing modules in a package that follows
this convention and passing the package name to `discover_rules()`.

### Configuration Helpers

```python
# tiredize/linter/utils.py
def validate_config(
    config: dict[str, Any],
    allowed: dict[str, str],
    required: Iterable[str],
    rule_id: str,
) -> None

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

`validate_config()` checks a rule's whole configuration block at the
top of `validate()`. It returns `None` on success and raises
`ValueError` on any of the three fault states in "Rule Configuration
Validation" below. `allowed` maps every accepted key to a type name
from the type vocabulary; `required` names the subset whose absence
would leave the rule inert; `rule_id` is named in every message.

The `get_config_*` accessors are type-safe retrievals from the same
dictionary. Each returns `None` if the key is missing **or** if the
value is the wrong type, and none of them raises. That ambiguity is
why they cannot police configuration themselves — the three fault
states have to be separated before an accessor is reached, which is
what `validate_config()` does.

Because `validate_config()` runs first, a `None` from an accessor
inside a rule means one thing only: an optional key was omitted,
and the rule should apply its own default. For a key the rule declared
required, the accessor cannot return `None` at all — presence and type
are already established.

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
- `./relative` -- resolves relative to the document's directory
  (`document.path.parent`) and checks file existence.
- `http(s)://` -- makes an HTTP request with the given options.

## File Layout

```
tiredize/linter/
├── __init__.py
├── engine.py         run_linter, _select_rules
├── utils.py          validate_config, get_config_*, check_url_valid
└── rules/
    ├── __init__.py   Rule, RuleFunc, discover_rules
    ├── _elements.py  element name to type mapping (private)
    ├── elements.py
    ├── line_length.py
    ├── links.py
    ├── tabs.py
    ├── trailing_whitespace.py
    └── unicode.py
```

## Rule Configuration Validation

A rule receives its whole configuration block as a dict, parsed from
the `--rules` YAML file. `validate_config()` checks that block before
the rule reads any of it.

### Fault States

Three states are errors. Each raises `ValueError` naming the rule id
and the offending key:

| State                                          | Example                        |
|------------------------------------------------|--------------------------------|
| A key the rule does not accept                 | `line_length: {max_length: 80}` |
| An accepted key holding a wrong-typed value    | `line_length: {maximum_length: "80"}` |
| A required key omitted                         | `line_length: {exclude: [code]}` |

An omitted **optional** key is legal; the rule falls back to its own
default.

The errors propagate out of `run_linter()` to the CLI, which prints
them to stderr and aborts the run with exit status `1` — see
`specifications/cli.md`. A configuration mistake is therefore a loud
failure, not a rule that quietly stops checking.

### Order of Reporting

Faults are reported in a fixed order — unknown keys, then omitted
required keys, then wrong-typed values — so the message for a given
configuration is deterministic. Unknown keys come first because a typo
is both the likeliest fault and the one that makes the others
misleading: a misspelled required key looks like an omission until its
real name is pointed out.

Only the first fault found is reported; `validate_config()` raises
rather than accumulating.

### Type Vocabulary

`_ALLOWED_KEYS` maps each key to one of five type names. Each
predicate mirrors the matching accessor, so a value `validate_config()`
accepts is a value that accessor will return rather than treat as
absent.

| Type name | Accepted Python value           | Accessor          |
|-----------|---------------------------------|-------------------|
| `bool`    | `bool`                          | `get_config_bool` |
| `dict`    | `dict`                          | `get_config_dict` |
| `int`     | `int`, excluding `bool`         | `get_config_int`  |
| `list`    | `list`                          | `get_config_list` |
| `str`     | `str`                           | `get_config_str`  |

`bool` is excluded from `int` because Python's `bool` is an `int`
subclass, so `maximum_length: true` would otherwise pass as an
integer.

### Classifying a Key as Required or Optional

The governing principle is that **enabling a rule must never be a
no-op**: if a rule appears in the configuration, it must do something.
So a key is *required* when its absence leaves the rule inert, and
*optional* when the rule still does its job without it.

Required means the key is **present**, not that it is truthy.
`links: {validate: false}` is legal and deliberately disables URL
checking; the key is there, so it is not the silent-typo failure mode.

Applied to the built-in rules:

| Rule                  | Required keys    | Optional keys                                      |
|-----------------------|------------------|----------------------------------------------------|
| `elements`            | `disallow`       | —                                                  |
| `line_length`         | `maximum_length` | `exclude`                                          |
| `links`               | `validate`       | `exclude`, `headers`, `timeout`, `valid_status_codes` |
| `tabs`                | —                | `allowed`                                          |
| `trailing_whitespace` | —                | `allowed`                                          |
| `unicode`             | `allowed`        | `exclude`                                          |

`tabs.allowed` and `trailing_whitespace.allowed` are optional because
those rules still forbid their target with the key absent. Every other
`allowed`-style key selects the mode the rule runs in, or supplies the
set it inspects, and without it the rule would inspect nothing.

### Key-Level Only

`validate_config()` checks keys and value types, nothing deeper.
Value-level checks a rule already performs — element names in
`exclude` or `disallow`, entries in `valid_status_codes` — run
afterwards, on values already confirmed to be of the right shape, and
raise `ValueError` from the rule itself.

## Design Decisions

- **One shared validator, not a hand-written check per rule.** The
  check lives in `validate_config()` in `tiredize/linter/utils.py` and
  every rule calls it. Writing it per rule is rejected: the messages
  drift between rules, and a new rule author who forgets it
  reintroduces the silent failure with nothing to catch it.

- **Key sets are declared in the rule module, not on `Rule`.** A rule
  already receives its whole config dict, so nothing forces its
  accepted keys onto the `Rule` dataclass, and discovery stays
  unchanged. The cost is that the engine cannot inspect a rule's key
  set without calling it.

- **Configuration mistakes are errors, not warnings.** All three fault
  states abort the run rather than degrading to a disabled rule. The
  alternative — reading an unrecognized or wrong-typed key as an absent
  one — lets a single typo switch a rule off across the whole tool
  while the run reports a clean exit status for a check that never
  executed.

- **Enabling a rule must never be a no-op.** This principle settles
  required versus optional. The alternative heuristic — classify by
  whether a key has a fallback default — cannot settle
  `elements.disallow` or `links.validate`, which have both a default
  and an early return.

- **Accessors keep returning `None` for both missing and wrong-typed
  keys.** They were left as they are rather than made to raise. The
  distinction the rules need is drawn once, up front, by
  `validate_config()`; pushing it into five accessors would duplicate
  it and still leave each rule to decide what to do about it.
