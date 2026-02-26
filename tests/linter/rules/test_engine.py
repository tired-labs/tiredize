from tiredize.linter.engine import run_linter
from tiredize.core_types import RuleNotFoundError
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document
import typing


def test_run_linter_unknown_rule_raises():
    markdown = """# Nothing to see here, move along."""
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, typing.Any] = {
        "the_rule_of_cool": {
            "enabled": True
        }
    }

    try:
        run_linter(document=doc, rule_configs=rule_configs)
        assert False, "Expected RuleNotFoundError was not raised"
    except RuleNotFoundError:
        pass


def test_run_linter_no_violations():
    markdown = """# Line Length Test (Passing)

    We have no issues here.
    Good luck hitting the limit of 80 characters per line!
    """
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, typing.Any] = {
        "line_length": {
            "maximum_length": 80
        }
    }

    results = run_linter(
        document=doc,
        rule_configs=rule_configs
    )

    assert len(results) == 0


def test_run_linter_undefined_rule():
    markdown = """# Nothing matters."""
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, typing.Any] = {
        "line_length": {
            "undefined_rule_for_testing": True
        }
    }

    results = run_linter(
        document=doc,
        rule_configs=rule_configs
    )
    assert len(results) == 0


def test_run_linter_one_violation():
    markdown = """# Line Length Test (Fail)

This line is absolutely, positively too long!
    """
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, typing.Any] = {
        "line_length": {
            "maximum_length": 25
        }
    }

    results = run_linter(
        document=doc,
        rule_configs=rule_configs
    )

    assert len(results) == 1

    res: RuleResult = results[0]
    assert res.rule_id == "line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.offset == 52
    assert res.position.length == 20


def test_run_linter_two_violations():
    markdown = """# Line Length Test (Fail)

This line is absolutely, positively too long!


Another overly long line is right here! What gives?!
"""
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, typing.Any] = {
        "line_length": {
            "maximum_length": 25
        }
    }

    results = run_linter(
        document=doc,
        rule_configs=rule_configs
    )

    assert len(results) == 2

    res: RuleResult = results[0]
    assert res.rule_id == "line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.offset == 52
    assert res.position.length == 20

    res = results[1]
    assert res.rule_id == "line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.offset == 100
    assert res.position.length == 27
