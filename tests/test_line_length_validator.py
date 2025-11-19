from tiredize.document import Document
from tiredize.validators.line_length import validate_line_length
import textwrap


def make_doc(md: str) -> Document:
    """Helper to build a Document from inline markdown."""
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


def make_schema(**line_length_cfg) -> dict:
    """
    Build a minimal schema fragment for line length tests.

    Example:
        make_schema(max=80, ignore_code_blocks=True)
    """
    return {
        "line_length": line_length_cfg,
    }


def test_line_length_flags_long_lines():
    md = """
    # Title

    This line is intentionally quite long to trigger the line length rule
    when the maximum is set relatively low.
    """

    doc = make_doc(md)
    schema = make_schema(max=60, ignore_code_blocks=True)

    results = validate_line_length(doc, schema)

    # Collect rule ids per line for easier assertions
    by_line = {}
    for r in results:
        by_line.setdefault(r.line, []).append(r.rule_id)

    # Title line should not be flagged
    # The long body line should be flagged with line_length
    assert any("line_length" in ids for ids in by_line.values())


def test_line_length_respects_ignore_code_blocks_true():
    md = """
    # Title

    ```python
    # This is an extremely long comment inside a fenced code block that
    # would normally violate any reasonable line length limit if it were
    # treated as plain text.
    ```

    Short line.
    """

    doc = make_doc(md)
    schema = make_schema(max=40, ignore_code_blocks=True)

    results = validate_line_length(doc, schema)

    # Nothing in the fenced block should be flagged
    # The only possible violations would come from non code lines
    assert all(r.rule_id != "line_length" for r in results)


def test_line_length_checks_code_blocks_when_not_ignored():
    md = """
    # Title

    ```python
    # This is an extremely long comment inside a fenced code block that
    # would normally violate any reasonable line length limit if it were
    # treated as plain text.
    ```

    Short line.
    """

    doc = make_doc(md)
    schema = make_schema(max=40, ignore_code_blocks=False)

    results = validate_line_length(doc, schema)

    # At least one violation should be reported from the long line in code
    assert any(r.rule_id == "line_length" for r in results)
