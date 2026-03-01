"""Tests for tiredize/linter/rules/tabs.py.

Covers tab detection, position accuracy, config edge cases, line
endings, unicode, idempotency, and state mutation.
"""

import copy

from tiredize.linter.rules.tabs import validate
from tiredize.markdown.types.document import Document


# ===================================================================
#  Tab detected, not allowed
# ===================================================================


def test_single_tab_not_allowed():
    """One tab on a single line is reported."""
    doc = Document()
    doc.load(text="# Heist Plan\n\tstep one: snacks\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].message == "Line contains a tab character."


def test_multiple_tabs_one_line():
    """Two tabs on the same line produce two violations."""
    doc = Document()
    doc.load(text="# Loot\n\tgold\tsilver\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2


def test_tabs_on_multiple_lines():
    """Tabs on separate lines each produce a violation."""
    doc = Document()
    doc.load(text="# Quests\n\tdragon\n\tgriffin\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2


# ===================================================================
#  Tab detected, allowed
# ===================================================================


def test_tabs_allowed_no_violations():
    """When allowed is True, tabs produce no violations."""
    doc = Document()
    doc.load(text="# Treasure\n\tgold coins\n")
    results = validate(doc, {"allowed": True})
    assert results == []


# ===================================================================
#  Tab position accuracy
# ===================================================================


def test_single_tab_position():
    """Reported offset matches the actual tab position in the document."""
    # "# Hi\n" = 5 chars, then "\there\n" has tab at index 5
    doc = Document()
    doc.load(text="# Hi\n\there\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 5
    assert results[0].position.length == 1


def test_multiple_tabs_one_line_positions():
    """Each tab on the same line has the correct offset."""
    # "# X\n" = 4 chars
    # "\tA\tB\n" -> first tab at 4, "A" at 5, second tab at 6
    doc = Document()
    doc.load(text="# X\n\tA\tB\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2
    assert results[0].position.offset == 4
    assert results[1].position.offset == 6


def test_tabs_across_lines_positions():
    """Tabs on different lines have correct document-level offsets."""
    # "# Y\n" = 4 chars
    # "\ta\n" = 3 chars -> tab at 4, cursor after = 7
    # "\tb\n" = 3 chars -> tab at 7
    doc = Document()
    doc.load(text="# Y\n\ta\n\tb\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2
    assert results[0].position.offset == 4
    assert results[1].position.offset == 7


def test_tab_mid_line_position():
    """A tab in the middle of a line has the correct offset."""
    # "# Z\n" = 4 chars
    # "ab\tcd\n" -> tab at 4 + 2 = 6
    doc = Document()
    doc.load(text="# Z\nab\tcd\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 6


# ===================================================================
#  Config edge cases
# ===================================================================


def test_config_missing_allowed_key():
    """Missing 'allowed' key means get_config_bool returns None (falsy).

    Tabs should be reported as violations."""
    doc = Document()
    doc.load(text="# Secret\n\thidden tab\n")
    results = validate(doc, {})
    assert len(results) == 1


def test_config_allowed_wrong_type():
    """Non-bool 'allowed' means get_config_bool returns None (falsy).

    Tabs should be reported as violations."""
    doc = Document()
    doc.load(text="# Oops\n\twrong type\n")
    results = validate(doc, {"allowed": "yes"})
    assert len(results) == 1


# ===================================================================
#  Empty document
# ===================================================================


def test_empty_document_no_violations():
    """A document with no tabs produces no violations."""
    doc = Document()
    doc.load(text="# Nothing here\n")
    results = validate(doc, {"allowed": False})
    assert results == []


# ===================================================================
#  CRLF line endings
# ===================================================================


def test_crlf_line_endings():
    """Tabs are detected correctly when lines end with \\r\\n."""
    # "# CR\r\n" = 6 chars, tab at offset 6
    doc = Document()
    doc.load(text="# CR\r\n\tstuff\r\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 6


# ===================================================================
#  Unicode (audit point 9)
# ===================================================================


def test_tab_with_non_ascii_characters():
    """Tab position is reported as character index, not byte offset."""
    # "# \u00e9\n" = 4 chars (# space e-acute newline)
    # "\t\u00fc\n" -> tab at offset 4
    doc = Document()
    doc.load(text="# \u00e9\n\t\u00fc\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 4


def test_tab_among_emoji():
    """Tab mixed with emoji reports correct character-based offset."""
    # "# \U0001f525\n" = 5 chars (# space fire newline) -- wait
    # Actually: '#' ' ' '\U0001f525' '\n' = 4 chars in Python
    # "\t\U0001f60e\n" -> tab at offset 4
    doc = Document()
    doc.load(text="# \U0001f525\n\t\U0001f60e\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 4


# ===================================================================
#  Idempotency (audit point 7)
# ===================================================================


def test_validate_idempotent():
    """Running validate twice on the same document yields identical results."""
    doc = Document()
    doc.load(text="# Same\n\ttwice\n")
    config = {"allowed": False}
    first = validate(doc, config)
    second = validate(doc, config)
    assert len(first) == len(second)
    for a, b in zip(first, second):
        assert a.position == b.position
        assert a.message == b.message


# ===================================================================
#  State mutation (audit point 8)
# ===================================================================


def test_validate_does_not_mutate_document():
    """validate() must not change the Document it receives."""
    doc = Document()
    doc.load(text="# Guard\n\tsafe\n")
    original_string = doc.string
    original_sections = len(doc.sections)
    validate(doc, {"allowed": False})
    assert doc.string == original_string
    assert len(doc.sections) == original_sections


def test_validate_does_not_mutate_config():
    """validate() must not change the config dict it receives."""
    doc = Document()
    doc.load(text="# Config\n\ttab here\n")
    config = {"allowed": False}
    config_copy = copy.deepcopy(config)
    validate(doc, config)
    assert config == config_copy


# ===================================================================
#  Partial failure / no early termination (audit point 10)
# ===================================================================


def test_all_lines_processed():
    """Every line in a multi-line document is checked for tabs."""
    lines = ["# Lines\n"] + [f"\tline{i}\n" for i in range(20)]
    doc = Document()
    doc.load(text="".join(lines))
    results = validate(doc, {"allowed": False})
    assert len(results) == 20
