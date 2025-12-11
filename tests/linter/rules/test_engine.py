from tiredize.linter.engine import run_linter
from tiredize.linter.types import RuleResult
from tiredize.markdown.types.document import Document


def test_run_linter_no_violations():
    # Build a simple document. Adjust ctor to match your real Document API.
    markdown = """# Line Length Test (Passing)

    We have no issues here.
    Good luck hitting the limit of 80 characters per line!
    """
    doc = Document()
    doc.load(text=markdown)

    # Config in the flat form the engine expects:
    # rule_id -> config dict
    rules_config = {
        "whitespace": {
            "line_length": {
                "max_length": 80,
            }
        }
    }

    # Run only this one rule, using the real rules package.
    results = run_linter(
        document=doc,
        rules_config=rules_config
    )

    # No violations.
    assert len(results) == 0


def test_run_linter_one_violation():
    # Build a simple document. Adjust ctor to match your real Document API.
    markdown = """# Line Length Test (Fail)

This line is absolutely, positively too long!
    """
    doc = Document()
    doc.load(text=markdown)

    # Config in the flat form the engine expects:
    # rule_id -> config dict
    rules_config = {
        "whitespace": {
            "line_length": {
                "max_length": 25,
            }
        }
    }

    # Run only this one rule, using the real rules package.
    results = run_linter(
        document=doc,
        rules_config=rules_config
    )

    # One violation: the second line.
    assert len(results) == 1

    res: RuleResult = results[0]
    assert res.rule_id == "whitespace.line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.line == 3
    assert res.position.offset == 25
    assert res.position.length == 20


def test_run_linter_two_violations():
    # Build a simple document. Adjust ctor to match your real Document API.
    markdown = """# Line Length Test (Fail)

This line is absolutely, positively too long!


Another overly long line is right here! What gives?!
"""
    doc = Document()
    doc.load(text=markdown)

    # Config in the flat form the engine expects:
    # rule_id -> config dict
    rules_config = {
        "whitespace": {
            "line_length": {
                "max_length": 25,
            }
        }
    }

    # Run only this one rule, using the real rules package.
    results = run_linter(
        document=doc,
        rules_config=rules_config
    )

    # One violation: the second line.
    assert len(results) == 2

    res: RuleResult = results[0]
    assert res.rule_id == "whitespace.line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.line == 3
    assert res.position.offset == 25
    assert res.position.length == 20

    res = results[1]
    assert res.rule_id == "whitespace.line_length"
    assert "exceeds maximum length" in res.message
    assert res.position.line == 6
    assert res.position.offset == 25
    assert res.position.length == 27
