from pathlib import Path
from tiredize.markdown.types.document import Document


def test_document_no_path_or_string():
    document = Document()
    try:
        document.load()
    except ValueError as e:
        assert str(e) == "Provide either 'path' or 'text'."


def test_document_both_path_and_string():
    document = Document()
    try:
        document.load(Path("fakefile.md"), "Some markdown text")
    except ValueError as e:
        assert str(e) == "Provide either 'path' or 'text', not both."


def test_document_load_from_string():
    md_text = r"""# Sample Document

    This is a sample markdown document.
"""

    document = Document()
    document.load(text=md_text)
    assert document._string == md_text
    assert document.frontmatter is None


def test_document_load_from_path():
    document = Document()
    test_path = r"c:/users/aprzybys/code/tired/tooling/tiredize/tests/" \
        "test-cases/good-frontmatter-and-markdown.md"
    document.load(Path(test_path))

    assert document.frontmatter is not None
