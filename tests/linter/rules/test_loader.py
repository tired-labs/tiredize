# Standard library
from __future__ import annotations

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.linter.rules import Rule
from tiredize.linter.rules import discover_rules
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
