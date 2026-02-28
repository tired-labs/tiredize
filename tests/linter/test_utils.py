# Standard library
from __future__ import annotations

# Local
from tiredize.linter.utils import check_url_valid
from tiredize.markdown.types.document import Document


# --- check_url_valid: relative URLs ---


def test_relative_url_resolves_to_parent_directory(tmp_path):
    """./sibling.md should resolve relative to the document's directory,
    not relative to the document file path itself."""
    doc_file = tmp_path / "reports" / "dragon-sighting.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("# Dragon Sighting")

    sibling = tmp_path / "reports" / "treasure-map.md"
    sibling.write_text("# Treasure Map")

    doc = Document()
    doc.path = doc_file

    is_valid, status, error = check_url_valid(doc, "./treasure-map.md")
    assert is_valid is True
    assert error is None


def test_relative_url_file_not_found(tmp_path):
    doc_file = tmp_path / "lonely-wizard.md"
    doc_file.write_text("# Lonely Wizard")

    doc = Document()
    doc.path = doc_file

    is_valid, status, error = check_url_valid(doc, "./nonexistent-spell.md")
    assert is_valid is False
    assert error == "relative file not found"


def test_relative_url_no_document_path():
    doc = Document()
    doc.path = None

    is_valid, status, error = check_url_valid(doc, "./ghost-file.md")
    assert is_valid is False
    assert "no path" in error
