# Standard library
from __future__ import annotations

# Local
from tiredize.markdown.types.list import List


# =========================================================================
#  List.extract() -- stub behavior
#  List is not yet implemented; extract() always returns an empty list.
# =========================================================================


def test_list_extract_returns_empty():
    """List.extract() is a stub. Returns empty list for any input."""
    text = "- item one\n- item two\n- item three\n"
    results = List.extract(text)
    assert results == []


def test_list_extract_empty_string():
    """List.extract() returns empty for empty string (line 16-17)."""
    results = List.extract("")
    assert results == []


def test_list_extract_non_list_content():
    """Stub returns empty even for non-list content."""
    text = "Just a paragraph of text."
    results = List.extract(text)
    assert results == []


def test_list_extract_with_base_offset():
    """base_offset is accepted but has no effect on stub."""
    text = "- item\n"
    results = List.extract(text, base_offset=100)
    assert results == []
