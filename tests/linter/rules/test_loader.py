from tiredize.linter.rules import discover_rules, Rule
from tiredize.linter.types import RuleResult
from tiredize.markdown.types.document import Document
from tiredize.types import Position


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
            line=500,
            offset=50,
            length=15
        ),
        rule_id="simple_rule"
    )
    assert result[0] == expected_result


def test_discover_rules_ignores_private_modules():
    rules = discover_rules("tests.test_cases.rules.02_private_rule")
    assert len(rules) == 0
