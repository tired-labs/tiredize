from tiredize.document import Document
from tiredize.validators.whitespace import validate_whitespace
import textwrap


def make_doc(md: str) -> Document:
    """Helper to build a Document from inline markdown."""
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


def make_schema(**whitespace_cfg) -> dict:
    """
    Build a minimal schema fragment for whitespace tests.

    Example:
      make_schema(trailing_ws=True, ignore_code_blocks=True)
    """
    return {
        "whitespace": whitespace_cfg,
    }


def test_trailing_whitespace_is_flagged():
    md = """
    # Title # noqa: W291    

    Body text. # noqa: W291    
    """

    doc = make_doc(md)
    schema = make_schema(trailing_ws=True)

    results = validate_whitespace(doc, schema)

    trailing = [r for r in results if r.rule_id == "trailing_ws"]
    assert len(trailing) == 2


def test_trailing_whitespace_respects_ignore_code_blocks_true():
    md = """
    # Title

    ```python
    def example():
        print("\tMy whitespace should be ignored.") # noqa: W291       
    ```

    Short line. # noqa: W291   
    """

    doc = make_doc(md)
    schema = make_schema(trailing_ws=True, ignore_code_blocks=True)

    results = validate_whitespace(doc, schema)

    trailing = [r for r in results if r.rule_id == "trailing_ws"]
    assert len(trailing) == 1


def test_tab_characters_are_flagged():
    md = """
    # Title

    Line with\ta tab in the middle.
    """

    doc = make_doc(md)
    schema = make_schema(tab_char=True)

    results = validate_whitespace(doc, schema)

    tab_results = [r for r in results if r.rule_id == "tab_char"]
    assert len(tab_results) == 1


def test_tab_characters_respects_ignore_code_blocks_true():
    md = """
    # Title

    ```python
    def example():
        print("\tThe tab in this line should be ignored.")
    ```

    \tNormal line.
    """

    doc = make_doc(md)
    schema = make_schema(tab_char=True, ignore_code_blocks=True)

    results = validate_whitespace(doc, schema)

    tab_results = [r for r in results if r.rule_id == "tab_char"]
    assert len(tab_results) == 1
