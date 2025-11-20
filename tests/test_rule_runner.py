from tiredize.document import Document
from tiredize.rule_runner import run_rules
from tiredize.types import RuleResult
import textwrap


def make_doc(md: str) -> Document:
    """Helper to build a Document from inline markdown."""
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


def test_run_rules_invokes_line_length_by_default():
    md = """
    # Title

    This line is intentionally very very long so that it will exceed a low
    maximum line length value when the validator runs.
    """

    doc = make_doc(md)

    schema = {
        # No "rules" section means everything in the registry is enabled
        "line_length": {
            "max": 60,
            "ignore_code_blocks": True,
        }
    }

    results = run_rules(doc, schema)

    assert isinstance(results, list)
    assert all(isinstance(r, RuleResult) for r in results)

    # At least one line_length violation should be present
    assert any(r.rule_id == "line_length" for r in results)


def test_run_rules_respects_rule_toggle_in_schema():
    md = """
    # Title

    This line is intentionally very very long so that it will exceed a low
    maximum line length value when the validator runs.
    """

    doc = make_doc(md)

    schema = {
        "line_length": {
            "max": 40,
            "ignore_code_blocks": True,
        },
        "rules": {
            "line_length": False,
        },
    }

    results = run_rules(doc, schema)

    # With the rule explicitly disabled, no findings should be returned
    assert results == []
