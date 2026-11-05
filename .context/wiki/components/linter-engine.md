# Linter Engine

## Overview

The linter engine discovers rule modules, selects the ones a rules file
enables, checks each rule's configuration, runs the rules against a
parsed document and stamps each finding with its rule id. It lives in
`tiredize/linter/`. The engine also provides the helpers rules share:
configuration checking, typed configuration accessors, the element
vocabulary and URL checking.

Each built-in rule's contract and behaviour is on its own `rule-` page, listed under Built-in Rules.
The engine reads the `Section` fields the [markdown
parser](./markdown-parser.md) fills in. Structural checks do not belong
here; they belong to the [markdown schema
validator](./markdown-schema-validator.md) (see [scope](../overview/scope.md)).

## Contracts and Interfaces

### Rules File

The file passed with `--rules` is a YAML mapping from rule id to that
rule's configuration mapping. A rule runs only when it has an entry.

```yaml
line_length:
  maximum_length: 80
  exclude: [code_block, table]
tabs: {}
links:
  validate: true
  timeout: 10
```

A rule that needs no keys is enabled with an empty mapping (`tabs: {}`);
an entry with nothing under it (`tabs:`) is YAML null and is a runtime
error. Every key below is checked by `validate_config()` before the rule
runs: an unknown key, a wrong type or a missing required key stops the
run (see Configuration Validation). "Type" uses that
function's vocabulary: `bool`, `int` (never a boolean), `list`, `dict`.

### Rules at a Glance

| Rule                  | Required keys    | Optional keys                                         |
|-----------------------|------------------|-------------------------------------------------------|
| `elements`            | `disallow`       | —                                                     |
| `line_length`         | `maximum_length` | `exclude`                                             |
| `links`               | `validate`       | `exclude`, `headers`, `timeout`, `valid_status_codes` |
| `tabs`                | —                | `allowed`                                             |
| `trailing_whitespace` | —                | `allowed`                                             |
| `unicode`             | `allowed`        | `exclude`                                             |

### Built-in Rules

| Rule                  | Page                                                   | Required keys    | Optional keys                                         |
|-----------------------|--------------------------------------------------------|------------------|-------------------------------------------------------|
| `elements`            | [rule-elements](./rule-elements.md)                    | `disallow`       | —                                                     |
| `line_length`         | [rule-line-length](./rule-line-length.md)              | `maximum_length` | `exclude`                                             |
| `links`               | [rule-links](./rule-links.md)                          | `validate`       | `exclude`, `headers`, `timeout`, `valid_status_codes` |
| `tabs`                | [rule-tabs](./rule-tabs.md)                            | —                | `allowed`                                             |
| `trailing_whitespace` | [rule-trailing-whitespace](./rule-trailing-whitespace.md) | —             | `allowed`                                             |
| `unicode`             | [rule-unicode](./rule-unicode.md)                      | `allowed`        | `exclude`                                             |

A new rule gets its own `rule-<id>.md` page with the same sections.

### Engine Entry Point

```python
# tiredize/linter/engine.py
def run_linter(
    document: Document,
    rule_configs: dict[str, dict[str, Any]] | None = None
) -> list[RuleResult]:
```

Discovers every rule with `discover_rules()`, keeps those with an entry
in `rule_configs`, runs each rule's `validate` function, and returns the
findings with `rule_id` set to the rule's id. A rule with no entry is
disabled. `None` enables nothing.

An id in `rule_configs` that matches no discovered rule raises
`RuleNotFoundError` (`tiredize/core_types.py`). A rule entry whose value
is not a mapping, including an empty entry such as `line_length:` with
nothing under it, raises `ValueError("Invalid configuration for rule
line_length: None")`. Neither the engine nor the `links` rule catches
an unexpected exception from a rule; it propagates to the caller, and
the [CLI](./cli.md) handles the ones it knows.

### Rule Discovery

```python
# tiredize/linter/rules/__init__.py
RuleFunc = Callable[[Document, dict[str, Any]], list[RuleResult]]

@dataclass(frozen=True)
class Rule:
    id: str
    func: RuleFunc
    description: str | None = None

def discover_rules(package: str | None = None) -> dict[str, Rule]:
```

Imports every non-private module (no leading `_`) directly in a package,
by default `tiredize.linter.rules`, and registers each one that has a
callable named `validate`. The rule id is the module's filename
(`line_length.py` gives `line_length`). The description is the
function's docstring.

`run_linter()` always discovers from the default package and the CLI
has no option to change it, so a custom rule reaches the CLI only by
being placed in `tiredize/linter/rules/` (an editable install or a fork).
The `package` argument serves Python callers of `discover_rules()`.

### Rule Module Convention

A rule module must:

1. Be non-private (filename not starting with `_`).
2. Expose `validate(document: Document, config: dict[str, Any]) ->
   list[RuleResult]`.
3. Return `RuleResult` instances with `rule_id=None`; the engine fills
   it in from the module name.
4. Declare the configuration keys it accepts and the subset it
   requires, and call `validate_config()` as the first statement of
   `validate()`, before reading any key.

Discovery checks only the first two, so requirement 4 is kept by
convention: a rule that skips it reads a mistyped key as an absent one
and silently checks nothing. Every built-in rule keeps it, and
`tests/linter/rules/test_loader.py` guards that for the built-in rules.

The declaration is module-level constants in the rule module:

```python
# tiredize/linter/rules/<rule_id>.py
_RULE_ID = "line_length"
_ALLOWED_KEYS = {
    "exclude": "list",
    "maximum_length": "int",
}
_REQUIRED_KEYS = ("maximum_length",)


def validate(document: Document, config: dict[str, Any]) -> list[RuleResult]:
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)
    ...
```

`_RULE_ID` is used only in configuration error messages; the engine
never reads it. It must equal the module filename, or configuration
errors name an id that appears nowhere in the user's rules file. A rule
that accepts no keys still calls `validate_config()` with an empty
`_ALLOWED_KEYS`, which makes any configuration of it an error.

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
def get_config_dict(config: dict[str, Any], key: str) -> dict[str, Any] | None
def get_config_list(config: dict[str, Any], key: str) -> list[str] | None
```

`validate_config()` returns `None` or raises `ValueError` naming the
rule id and the key (see Configuration Validation). Each `get_config_*`
accessor returns `None` when the key is missing **or** holds the wrong
type, and never raises. Because `validate_config()` has already run, a
`None` inside a rule means only that an optional key was omitted; a
required key cannot return `None`.

### URL Checking

```python
# tiredize/linter/utils.py
def check_url_valid(
    document: Document,
    url: str,
    timeout: float | None = None,
    headers: dict[str, Any] | None = None,
    allow_redirects: bool | None = None,
    verify_ssl: bool | None = None,
    valid_status_codes: list[int | str] | None = None,
) -> tuple[bool, int | None, str | None]:
```

Returns `(is_valid, status_code, error_message)` and never raises.

- A target starting with `#` is valid when it equals a section header's
  slug (see [the parser](./markdown-parser.md)).
- A target starting with `.` is resolved against the document's
  directory and is valid when that file exists. A document loaded from
  text, with no path, fails.
- Anything else is fetched with `requests.get`, following redirects by
  default, with the header `User-Agent: tiredize-link-checker/1.0`
  unless `headers` is given. `valid_status_codes` lists exact codes or
  class wildcards such as `'2xx'`; `None` accepts every 2xx and 3xx.

The function does not filter by scheme: a `mailto:` or a scheme-less
`example.com` is attempted as an HTTP request and reported as a
failure. The `links` rule decides what reaches it.

### Element Vocabulary

```python
# tiredize/linter/rules/_elements.py
_ELEMENT_LABELS: dict[str, str]                     # name -> label in findings
_ELEMENT_MAP: dict[str, Callable[[Section], list]]  # name -> elements
```

The names accepted in `elements.disallow`, `line_length.exclude` and
`unicode.exclude`:

| Name                   | `Section` field         | Label                 |
|------------------------|-------------------------|-----------------------|
| `autolink`             | `autolinks`             | Autolink              |
| `autolink_extended`    | `autolinks_extended`    | Extended autolink     |
| `code_block`           | `code_block`            | Fenced code block     |
| `code_inline`          | `code_inline`           | Inline code           |
| `header`               | `header`                | Header                |
| `image_inline`         | `images_inline`         | Inline image          |
| `image_reference`      | `images_reference`      | Reference-style image |
| `link_inline`          | `links_inline`          | Inline link           |
| `link_reference`       | `links_reference`       | Reference-style link  |
| `quoteblock`           | `quoteblocks`           | Blockquote            |
| `reference_definition` | `reference_definitions` | Reference definition  |
| `table`                | `tables`                | Table                 |

Any other name raises `ValueError` (`Unknown element name in disallow:
'…'`, or `… in exclude: '…'`) when the rule runs. There are no aliases.

## File Layout

```
tiredize/linter/
├── engine.py         run_linter, _select_rules
├── utils.py          validate_config, get_config_*, check_url_valid
└── rules/
    ├── __init__.py   Rule, RuleFunc, discover_rules
    ├── _elements.py  element vocabulary (private)
    ├── elements.py
    ├── line_length.py
    ├── links.py
    ├── tabs.py
    ├── trailing_whitespace.py
    └── unicode.py
```

## Configuration Validation

A rule receives its whole block from the `--rules` YAML file as a dict.
`validate_config()` checks it before the rule reads any of it.

### Fault States

Each raises `ValueError` naming the rule id and the key:

| State                                | Example                                |
|--------------------------------------|----------------------------------------|
| A key the rule does not accept       | `line_length: {max_length: 80}`        |
| An accepted key with a wrong type    | `line_length: {maximum_length: "80"}`  |
| A required key omitted               | `line_length: {exclude: [code_block]}` |

An omitted optional key is legal; the rule uses its own default. A
wrong-typed optional key is still an error. The [CLI](./cli.md) prints
the error and stops the run with status `1`.

Faults are reported in a fixed order (unknown keys, then omitted
required keys, then wrong types), and only the first is reported.

### Type Vocabulary

| Type name | Accepted value         | Accessor          |
|-----------|------------------------|-------------------|
| `bool`    | `bool`                 | `get_config_bool` |
| `dict`    | `dict`                 | `get_config_dict` |
| `int`     | `int`, excluding `bool`| `get_config_int`  |
| `list`    | `list`                 | `get_config_list` |
| `str`     | `str`                  | `get_config_str`  |

Each type check mirrors its accessor, so a value `validate_config()`
accepts is one the accessor returns. `bool` is excluded from `int`
because Python's `bool` subclasses `int`; `maximum_length: true` would
otherwise pass, and `True` is not `1`.

`validate_config()` checks keys and value types only. A `list` or
`dict` is not checked entry by entry; each built-in rule checks its own
entries (element names, status codes, exclude patterns) afterwards and
raises `ValueError` itself.

### Required or Optional

**Enabling a rule must never be a no-op.** A key is required when its
absence leaves the rule inert, and optional when the rule still does
its job without it. Required means present, not truthy:
`links: {validate: false}` deliberately turns link checking off. Each
rule page gives the reason for its own classification.

## Design Decisions

- **One shared validator, not a check written per rule.** Per-rule
  checks drift in their messages, and a new rule author who forgets one
  brings back the silent failure.
- **Key sets are declared in the rule module, not on `Rule`.** A rule
  already receives its whole config, and discovery stays unchanged. The
  cost is that the engine cannot see a rule's keys without calling it.
- **Configuration mistakes are errors, not warnings.** Reading an
  unknown or wrong-typed key as absent lets one typo switch a rule off
  everywhere while the run exits clean. The project's own CLI tests
  once shipped such a typo unnoticed.
- **Enabling a rule must never be a no-op.** This settles required
  versus optional. Classifying by "has a fallback default" cannot settle
  `elements.disallow` or `links.validate`, which have both a default and
  an early return.
- **Unknown keys are reported first,** because a typo makes the other
  faults misleading: a misspelled required key reads as an omission.
- **Accessors keep returning `None` for missing and wrong-typed keys.**
  The distinction is drawn once by `validate_config()`; pushing it into
  five accessors would duplicate it.
- **The engine, not `validate_config()`, rejects a non-mapping rule
  block,** so one condition never gets two messages.
- **No aliases for element names.** The vocabulary is small, the load
  error is explicit, and old names would compete with the GFM terms in
  the documentation.

## Open Questions

- An empty rule block (`line_length:`) is the likeliest way to omit a required key, yet its message does not name the missing key.
- Nothing stops a custom rule that skips `validate_config()` from loading.
- `test_loader.py` requires every built-in rule to declare at least one key, while the convention allows a rule with none.
