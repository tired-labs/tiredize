"""Tests for tiredize/linter/rules/trailing_whitespace.py.

Covers trailing whitespace detection, position accuracy, config edge
cases, whitespace-only lines, line endings, unicode, idempotency, and
state mutation.
"""

import copy

from tiredize.linter.rules.trailing_whitespace import validate
from tiredize.markdown.types.document import Document


# ===================================================================
#  Trailing whitespace detected, not allowed
# ===================================================================


def test_single_trailing_space():
    """One trailing space on a line is reported."""
    doc = Document()
    doc.load(text="# Ghosts \nare real\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].message == "Line contains trailing whitespace."


def test_multiple_trailing_spaces():
    """Multiple trailing spaces on one line produce one violation."""
    doc = Document()
    doc.load(text="# Spooky   \nstuff\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.length == 3


def test_trailing_tab():
    """A trailing tab character is reported as trailing whitespace."""
    doc = Document()
    doc.load(text="# Phantom\t\nvanished\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.length == 1


def test_trailing_whitespace_on_multiple_lines():
    """Each line with trailing whitespace gets its own violation."""
    doc = Document()
    doc.load(text="# A \n# B \n# C \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 3


# ===================================================================
#  Trailing whitespace detected, allowed
# ===================================================================


def test_trailing_whitespace_allowed_no_violations():
    """When allowed is True, trailing whitespace produces no violations."""
    doc = Document()
    doc.load(text="# Cozy   \nblanket \n")
    results = validate(doc, {"allowed": True})
    assert results == []


# ===================================================================
#  Position accuracy
# ===================================================================


def test_trailing_space_position_offset():
    """Reported offset points to the start of the trailing whitespace."""
    # "# Hi \n" -> "# Hi" is 4 chars, trailing space at index 4
    doc = Document()
    doc.load(text="# Hi \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 4
    assert results[0].position.length == 1


def test_trailing_spaces_position_length():
    """Length covers all trailing whitespace characters."""
    # "# OK   \n" -> "# OK" is 4 chars, 3 trailing spaces at index 4
    doc = Document()
    doc.load(text="# OK   \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 4
    assert results[0].position.length == 3


def test_trailing_whitespace_second_line_position():
    """Offset on a later line accounts for prior line lengths."""
    # "# AA\n" = 5 chars
    # "bb  \n" -> trailing starts at offset 5 + 2 = 7, length 2
    doc = Document()
    doc.load(text="# AA\nbb  \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 7
    assert results[0].position.length == 2


# ===================================================================
#  Config edge cases
# ===================================================================


def test_config_missing_allowed_key():
    """Missing 'allowed' key means None (falsy), whitespace reported."""
    doc = Document()
    doc.load(text="# Whoops \n")
    results = validate(doc, {})
    assert len(results) == 1


def test_config_allowed_wrong_type():
    """Non-bool 'allowed' returns None (falsy), so whitespace is reported."""
    doc = Document()
    doc.load(text="# Nope \n")
    results = validate(doc, {"allowed": 42})
    assert len(results) == 1


# ===================================================================
#  Empty document
# ===================================================================


def test_empty_document_no_violations():
    """A document with no trailing whitespace produces no violations."""
    doc = Document()
    doc.load(text="# Clean\n")
    results = validate(doc, {"allowed": False})
    assert results == []


# ===================================================================
#  Line with only whitespace
# ===================================================================


def test_whitespace_only_line():
    """A line containing only spaces is fully reported as trailing."""
    # "# Top\n" = 6 chars
    # "   \n" -> stripped = "", offset_in_line = 0, length = 3
    # So offset = 6, length = 3
    doc = Document()
    doc.load(text="# Top\n   \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 6
    assert results[0].position.length == 3


def test_tab_only_line():
    """A line containing only a tab is fully reported as trailing."""
    doc = Document()
    doc.load(text="# Top\n\t\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 6
    assert results[0].position.length == 1


# ===================================================================
#  CRLF line endings
# ===================================================================


def test_crlf_trailing_space():
    """Trailing spaces before \\r\\n are detected and \\r is not counted."""
    # "# CR\r\n" = 6 chars
    # "ok \r\n" -> line_text = "ok " (after stripping \r\n), trailing at
    # offset 6 + 2 = 8, length 1
    doc = Document()
    doc.load(text="# CR\r\nok \r\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 8
    assert results[0].position.length == 1


# ===================================================================
#  Unicode (audit point 9)
# ===================================================================


def test_trailing_space_after_non_ascii():
    """Trailing space after accented characters reports correct position."""
    # "# caf\u00e9 \n" -> "# caf\u00e9" is 6 chars, trailing at index 6
    doc = Document()
    doc.load(text="# caf\u00e9 \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 6
    assert results[0].position.length == 1


def test_trailing_space_after_emoji():
    """Trailing space after emoji reports character-based position."""
    # "# \U0001f680 \n" -> "# \U0001f680" is 3 chars, trailing at index 3
    doc = Document()
    doc.load(text="# \U0001f680 \n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.offset == 3
    assert results[0].position.length == 1


# ===================================================================
#  Idempotency (audit point 7)
# ===================================================================


def test_validate_idempotent():
    """Running validate twice yields identical results."""
    doc = Document()
    doc.load(text="# Again \nand again \n")
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
    """validate() must not change the Document."""
    doc = Document()
    doc.load(text="# Vault \nsecret \n")
    original_string = doc.string
    original_sections = len(doc.sections)
    validate(doc, {"allowed": False})
    assert doc.string == original_string
    assert len(doc.sections) == original_sections


def test_validate_does_not_mutate_config():
    """validate() must not change the config dict."""
    doc = Document()
    doc.load(text="# Lock \n")
    config = {"allowed": False}
    config_copy = copy.deepcopy(config)
    validate(doc, config)
    assert config == config_copy


# ===================================================================
#  Partial failure / no early termination (audit point 10)
# ===================================================================


def test_all_lines_processed():
    """Every line in a multi-line document is checked."""
    lines = ["# Lines\n"] + [f"line{i} \n" for i in range(20)]
    doc = Document()
    doc.load(text="".join(lines))
    results = validate(doc, {"allowed": False})
    assert len(results) == 20
