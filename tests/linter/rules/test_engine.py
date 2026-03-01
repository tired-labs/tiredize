# Standard library
from __future__ import annotations
import copy
from typing import Any
from unittest.mock import patch

# Third-party
import pytest

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


# ===================================================================
#  engine.py gap: non-dict rule config raises ValueError (line 58)
# ===================================================================


def test_run_linter_non_dict_config_raises_value_error():
    """Passing a non-dict as a rule's config triggers ValueError."""
    doc = Document()
    doc.load(text="# Test\n")
    with pytest.raises(ValueError, match="Invalid configuration"):
        run_linter(document=doc, rule_configs={"tabs": "not-a-dict"})


# engine.py line 64: the isinstance(rule, Rule) check is unreachable
# from the public API. _select_rules always stores a Rule object
# from the discovered rules dict, so active_rules[rule_id]["rule"]
# is guaranteed to be a Rule. No test needed; documented here.


# ===================================================================
#  State mutation (audit point 8)
# ===================================================================


def test_run_linter_does_not_mutate_rule_configs():
    """run_linter must not change the rule_configs dict."""
    doc = Document()
    doc.load(text="# Mutation test\n\ttab here\n")
    configs = {"tabs": {"allowed": False}}
    configs_copy = copy.deepcopy(configs)
    run_linter(document=doc, rule_configs=configs)
    assert configs == configs_copy


# ===================================================================
#  Partial failure (audit point 10)
# ===================================================================


def test_run_linter_rule_exception_propagates():
    """If rule 2 of 3 raises, the entire call fails.

    run_linter does not catch exceptions from rule validate()
    functions. An unexpected exception propagates and remaining rules
    are not executed. This documents actual behavior: results from
    rule 1 are lost and rule 3 never runs.
    """
    doc = Document()
    doc.load(text="# Kaboom\n\ttab\n")

    def exploding_validate(document, config):
        raise RuntimeError("rule exploded")

    with patch(
        "tiredize.linter.rules.tabs.validate",
        side_effect=exploding_validate,
    ):
        with pytest.raises(RuntimeError, match="rule exploded"):
            run_linter(
                document=doc,
                rule_configs={
                    "line_length": {"maximum_length": 80},
                    "tabs": {"allowed": False},
                    "trailing_whitespace": {"allowed": False},
                }
            )
