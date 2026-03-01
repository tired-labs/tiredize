# Standard library
from __future__ import annotations
from typing import Any

# Local
from tiredize.core_types import RuleNotFoundError
from tiredize.core_types import RuleResult
from tiredize.linter.engine import run_linter
from tiredize.markdown.types.document import Document


def test_run_linter_unknown_rule_raises():
    markdown = """# Nothing to see here, move along."""
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, Any] = {
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

    rule_configs: dict[str, Any] = {
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

    rule_configs: dict[str, Any] = {
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

    rule_configs: dict[str, Any] = {
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

    rule_configs: dict[str, Any] = {
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


def test_run_linter_none_configs():
    """Passing rule_configs=None disables all rules and returns no results."""
    doc = Document()
    doc.load(text="# Anything\n\tshould not matter\n")
    results = run_linter(document=doc, rule_configs=None)
    assert results == []


def test_run_linter_empty_configs():
    """An empty rule_configs dict means no rules selected, no results."""
    doc = Document()
    doc.load(text="# Doesn't matter\n\ttabs everywhere\t\n")
    results = run_linter(document=doc, rule_configs={})
    assert results == []


def test_run_linter_multiple_rules():
    """Multiple rules can be active simultaneously and each stamps its id."""
    markdown = "# Cramped\n\tindented and way too long for the limit\n"
    doc = Document()
    doc.load(text=markdown)

    rule_configs: dict[str, Any] = {
        "tabs": {"allowed": False},
        "line_length": {"maximum_length": 10},
    }

    results = run_linter(document=doc, rule_configs=rule_configs)
    rule_ids = {r.rule_id for r in results}
    assert "tabs" in rule_ids
    assert "line_length" in rule_ids


def test_run_linter_rule_id_stamped_on_results():
    """The engine replaces each result's rule_id with the discovered id."""
    doc = Document()
    doc.load(text="# Stamp test\n\thas a tab\n")
    results = run_linter(
        document=doc,
        rule_configs={"tabs": {"allowed": False}}
    )
    assert len(results) >= 1
    for r in results:
        assert r.rule_id == "tabs"
