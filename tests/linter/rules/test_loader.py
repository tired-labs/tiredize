from tiredize.linter.rules import discover_rules, Rule
from tiredize.linter.types import RuleResult
from tiredize.markdown.types.document import Document
from tiredize.types import Position


def test_discover_rules_no_rules():
    rules = discover_rules("tests.test_cases.rules.00_no_rules")
    assert len(rules) == 0


def test_discover_rules_finds_simple_rule():
    rules = discover_rules("tests.test_cases.rules.01_simple_rules")
    assert len(rules) == 1
    assert "test.simple" in rules

    rule_def = rules["test.simple"]
    assert isinstance(rule_def, Rule)
    assert rule_def.id == "test.simple"
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
        rule_id="test.simple"
    )
    assert result[0] == expected_result


def test_discover_rules_ignores_private_modules():
    rules = discover_rules("tests.test_cases.rules.02_private_rules")
    assert len(rules) == 0


def test_discover_rules_multiple_rules_one_file():
    rules = discover_rules("tests.test_cases.rules.03_multiple_rules_one_file")
    assert len(rules) == 2

    assert "multiple.first" in rules
    rule_def = rules["multiple.first"]
    assert isinstance(rule_def, Rule)
    assert rule_def.id == "multiple.first"
    assert rule_def.description == "Simple example rule (#1) used for testing."
    assert callable(rule_def.func)
    result = rule_def.func(Document(), {})
    assert len(result) == 1
    expected_result = RuleResult(
        message="This is test rule #1.",
        position=Position(
            line=111,
            offset=11,
            length=11
        ),
        rule_id="multiple.first"
    )
    assert result[0] == expected_result

    assert "multiple.second" in rules
    rule_def = rules["multiple.second"]
    assert isinstance(rule_def, Rule)
    assert rule_def.id == "multiple.second"
    assert rule_def.description == "Simple example rule (#2) used for testing."
    assert callable(rule_def.func)
    result = rule_def.func(Document(), {})
    assert len(result) == 1
    expected_result = RuleResult(
        message="This is test rule #2.",
        position=Position(
            line=222,
            offset=22,
            length=22
        ),
        rule_id="multiple.second"
    )
    assert result[0] == expected_result


