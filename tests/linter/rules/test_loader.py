# Standard library
from __future__ import annotations
import importlib

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.rules import Rule
from tiredize.linter.rules import discover_rules
from tiredize.linter.utils import _CONFIG_TYPE_CHECKS
from tiredize.markdown.types.document import Document


def test_discover_rules_no_rules():
    rules = discover_rules("tests.test_cases.rules.00_no_rule")
    assert len(rules) == 0


def test_discover_rules_finds_simple_rule():
    rules = discover_rules("tests.test_cases.rules.01_simple_rule")
    assert len(rules) == 1
    assert "simple_rule" in rules

    rule_def = rules["simple_rule"]
    assert isinstance(rule_def, Rule)
    assert rule_def.id == "simple_rule"
    assert rule_def.description == "Simple example rule used for testing."
    assert callable(rule_def.func)
    result = rule_def.func(Document(), {})
    assert len(result) == 1
    expected_result = RuleResult(
        message="This is a simple test rule.",
        position=Position(
            offset=50,
            length=15
        ),
        rule_id="simple_rule"
    )
    assert result[0] == expected_result


def test_discover_rules_ignores_private_modules():
    rules = discover_rules("tests.test_cases.rules.02_private_rule")
    assert len(rules) == 0


def test_discover_rules_skips_subpackages():
    """Subpackages inside a rules package are not descended into."""
    rules = discover_rules("tests.test_cases.rules.03_with_subpackage")
    # Only top_rule should be found, not nested_pkg/hidden_rule
    assert len(rules) == 1
    assert "top_rule" in rules
    assert "hidden_rule" not in rules


def test_discover_rules_plain_module_returns_empty():
    """Passing a plain module (not a package) returns no rules."""
    rules = discover_rules("tiredize.linter.rules.tabs")
    assert len(rules) == 0


def test_discover_rules_default_package():
    """Calling discover_rules() with no argument discovers built-in rules."""
    rules = discover_rules()
    # The project ships at least these four rules
    for rule_id in ("line_length", "links", "tabs", "trailing_whitespace"):
        assert rule_id in rules, f"Expected built-in rule '{rule_id}'"
    # Each discovered rule should be a proper Rule with a callable
    for rule_id, rule in rules.items():
        assert isinstance(rule, Rule)
        assert callable(rule.func)


# ===================================================================
#  Rule-module configuration convention
#
#  Every built-in rule declares the keys it accepts and the subset it
#  requires, and calls validate_config as the first thing its
#  validate() does. These guards make a new rule module that skips
#  the declaration fail, rather than silently swallowing typos in its
#  configuration. See "Validating rule configuration" in
#  .context/issues/main-module-exit-code.md.
# ===================================================================


# One legal value per declared type, used to build the smallest
# configuration a rule will accept.
_SAMPLE_VALUES: dict[str, object] = {
    "bool": False,
    "dict": {},
    "int": 1,
    "list": [],
    "str": "",
}


def _rule_module(rule_id: str):
    """The module a built-in rule id was discovered from."""
    return importlib.import_module(f"tiredize.linter.rules.{rule_id}")


def _minimal_config(rule_id: str) -> dict[str, object]:
    """The smallest configuration block the rule accepts."""
    module = _rule_module(rule_id)
    return {
        key: _SAMPLE_VALUES[module._ALLOWED_KEYS[key]]
        for key in module._REQUIRED_KEYS
    }


# Rules that require at least one key. tabs and trailing_whitespace
# require none: with `allowed` absent they still forbid what they
# exist to forbid, so enabling them is never a no-op.
_RULES_WITH_REQUIRED_KEYS = sorted(
    rule_id
    for rule_id in discover_rules()
    if _rule_module(rule_id)._REQUIRED_KEYS
)


def test_some_built_in_rule_requires_a_key():
    """Guard: the missing-required-key case below is not vacuous."""
    assert _RULES_WITH_REQUIRED_KEYS


@pytest.mark.parametrize("rule_id", sorted(discover_rules()))
def test_built_in_rule_declares_its_configuration_keys(rule_id):
    """Each rule module declares its id and its key sets."""
    module = _rule_module(rule_id)
    assert module._RULE_ID == rule_id, (
        "the declared rule id must match the module name the loader "
        "derives the id from"
    )
    assert isinstance(module._ALLOWED_KEYS, dict)
    assert module._ALLOWED_KEYS, "a rule with no keys cannot be configured"
    for type_name in module._ALLOWED_KEYS.values():
        assert type_name in _CONFIG_TYPE_CHECKS
    assert set(module._REQUIRED_KEYS) <= set(module._ALLOWED_KEYS)


@pytest.mark.parametrize("rule_id", sorted(discover_rules()))
def test_built_in_rule_accepts_its_minimal_config(rule_id):
    """The required keys alone are a legal configuration.

    Whether the sample values produce findings is beside the point;
    what matters is that the block is accepted rather than rejected.
    """
    doc = Document()
    doc.load(text="# Nothing To See Here\n")
    results = discover_rules()[rule_id].func(doc, _minimal_config(rule_id))
    assert isinstance(results, list)


@pytest.mark.parametrize("rule_id", sorted(discover_rules()))
def test_built_in_rule_rejects_an_unknown_key(rule_id):
    """No rule may quietly swallow a key it does not accept."""
    doc = Document()
    doc.load(text="# Nothing To See Here\n")
    config = _minimal_config(rule_id)
    config["snooze_button"] = True
    with pytest.raises(ValueError) as excinfo:
        discover_rules()[rule_id].func(doc, config)
    message = str(excinfo.value)
    assert rule_id in message
    assert "snooze_button" in message


@pytest.mark.parametrize("rule_id", _RULES_WITH_REQUIRED_KEYS)
def test_built_in_rule_rejects_a_missing_required_key(rule_id):
    """Dropping any required key is an error naming that key."""
    doc = Document()
    doc.load(text="# Nothing To See Here\n")
    module = _rule_module(rule_id)
    for missing in module._REQUIRED_KEYS:
        config = _minimal_config(rule_id)
        del config[missing]
        with pytest.raises(ValueError) as excinfo:
            discover_rules()[rule_id].func(doc, config)
        message = str(excinfo.value)
        assert rule_id in message
        assert missing in message
