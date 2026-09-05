"""Tests for tiredize/linter/rules/unicode.py.

Covers the allowed/forbidden modes, exclude behaviour, position
accuracy, config edge cases, and interaction with the rule engine.
"""

import pytest

from tiredize.linter.rules.unicode import validate
from tiredize.markdown.types.document import Document


# ===================================================================
#  Config gating
# ===================================================================


# ===================================================================
#  Configuration validation (key level)
#
#  `allowed` is required: without it the rule inspects nothing, so
#  enabling `unicode` would be a no-op. See "Validating rule
#  configuration" in .context/issues/main-module-exit-code.md.
# ===================================================================


def test_missing_allowed_raises():
    """Enabling the rule without `allowed` would check nothing."""
    doc = Document()
    doc.load(text="# Héllo\n\ncafé\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {})
    message = str(excinfo.value)
    assert "unicode" in message
    assert "allowed" in message


def test_allowed_wrong_type_raises():
    """A non-bool 'allowed' is a configuration error, not a no-op."""
    doc = Document()
    doc.load(text="# Héllo\n\ncafé\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {"allowed": "yes"})
    message = str(excinfo.value)
    assert "unicode" in message
    assert "allowed" in message


def test_unknown_key_raises():
    """A key the rule does not accept is an error."""
    doc = Document()
    doc.load(text="# Héllo\n\ncafé\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {"allowed": True, "snooze_button": True})
    message = str(excinfo.value)
    assert "unicode" in message
    assert "snooze_button" in message


def test_unknown_key_reported_before_bad_element_name():
    """Key-level validation runs before the value-level check."""
    doc = Document()
    doc.load(text="# Héllo\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {
            "allowed": False,
            "exclude": ["bogus_element"],
            "snooze_button": True,
        })
    assert "snooze_button" in str(excinfo.value)


# ===================================================================
#  allowed: True  (unicode permitted everywhere)
# ===================================================================


def test_allowed_true_no_unicode_no_violations():
    """ASCII-only document with allowed=True produces no violations."""
    doc = Document()
    doc.load(text="# Hello\n\nplain text\n")
    assert validate(doc, {"allowed": True}) == []


def test_allowed_true_unicode_no_violations():
    """Unicode present with allowed=True produces no violations."""
    doc = Document()
    doc.load(text="# Héllo\n\ncafé au lait\n")
    assert validate(doc, {"allowed": True}) == []


# ===================================================================
#  allowed: False  (unicode forbidden everywhere)
# ===================================================================


def test_allowed_false_no_unicode_no_violations():
    """ASCII-only document with allowed=False produces no violations."""
    doc = Document()
    doc.load(text="# Hello\n\nplain text\n")
    assert validate(doc, {"allowed": False}) == []


def test_allowed_false_single_unicode_char_flagged():
    """One unicode character with allowed=False produces one violation."""
    doc = Document()
    doc.load(text="# Café\n\nsome text\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert "é" in results[0].message
    assert "U+00E9" in results[0].message


def test_allowed_false_multiple_unicode_chars_each_flagged():
    """Each unicode character produces a separate violation."""
    doc = Document()
    doc.load(text="# Hello\n\nüber café\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2


def test_allowed_false_unicode_in_header_flagged():
    """Unicode in a header is flagged when allowed=False."""
    doc = Document()
    doc.load(text="# Résumé\n\nplain body\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 2


# ===================================================================
#  Position accuracy
# ===================================================================


def test_violation_position_points_to_unicode_char():
    """The violation offset lands exactly on the unicode character."""
    doc = Document()
    doc.load(text="# Hello\n\ncafé\n")
    results = validate(doc, {"allowed": False})
    assert len(results) == 1
    assert results[0].position.length == 1
    assert doc.string[results[0].position.offset] == "é"


# ===================================================================
#  allowed: True + exclude  (unicode forbidden only in excluded elements)
# ===================================================================


def test_allowed_true_exclude_header_unicode_in_body_ok():
    """With allowed=True and header excluded, unicode in body is fine."""
    doc = Document()
    doc.load(text="# Hello\n\ncafé\n")
    results = validate(doc, {"allowed": True, "exclude": ["header"]})
    assert results == []


def test_allowed_true_exclude_header_unicode_in_header_flagged():
    """With allowed=True and header excluded, unicode in header is flagged."""
    doc = Document()
    doc.load(text="# Résumé\n\nplain body\n")
    results = validate(doc, {"allowed": True, "exclude": ["header"]})
    assert len(results) == 2
    for r in results:
        assert "U+00E9" in r.message


def test_allowed_true_exclude_header_mixed_violations_only_in_header():
    """Only the header unicode violations are reported."""
    doc = Document()
    doc.load(text="# Héro\n\ncafé and über\n")
    results = validate(doc, {"allowed": True, "exclude": ["header"]})
    assert len(results) == 1
    assert doc.string[results[0].position.offset] == "é"


# ===================================================================
#  allowed: False + exclude  (unicode allowed only in excluded elements)
# ===================================================================


def test_allowed_false_exclude_header_unicode_in_body_flagged():
    """With allowed=False and header excluded, unicode in body is flagged."""
    doc = Document()
    doc.load(text="# Hello\n\ncafé\n")
    results = validate(doc, {"allowed": False, "exclude": ["header"]})
    assert len(results) == 1
    assert doc.string[results[0].position.offset] == "é"


def test_allowed_false_exclude_header_unicode_in_header_ok():
    """With allowed=False and header excluded, unicode in header is fine."""
    doc = Document()
    doc.load(text="# Résumé\n\nplain body\n")
    results = validate(doc, {"allowed": False, "exclude": ["header"]})
    assert results == []


def test_allowed_false_exclude_header_mixed_violations_only_in_body():
    """Only body unicode violations are reported; header unicode is exempt."""
    doc = Document()
    doc.load(text="# Héro\n\ncafé and über\n")
    results = validate(doc, {"allowed": False, "exclude": ["header"]})
    assert len(results) == 2
    offsets = {r.position.offset for r in results}
    header_offset = doc.string.index("é")
    assert header_offset not in offsets


# ===================================================================
#  exclude: multiple element types
# ===================================================================


def test_allowed_false_exclude_code_block_permits_unicode_in_code():
    """Unicode inside a fenced code block is exempt when excluded."""
    md = (
        "# Hello\n\n"
        "```\ncafé\n```\n\n"
        "plain body\n"
    )
    doc = Document()
    doc.load(text=md)
    results = validate(doc, {"allowed": False, "exclude": ["code_block"]})
    assert results == []


def test_allowed_false_exclude_multiple_elements():
    """Multiple element types can be excluded simultaneously."""
    md = (
        "# Héro\n\n"
        "`café`\n\n"
        "plain body\n"
    )
    doc = Document()
    doc.load(text=md)
    results = validate(doc, {
        "allowed": False,
        "exclude": ["header", "code_inline"],
    })
    assert results == []


# ===================================================================
#  Config validation
# ===================================================================


def test_unknown_exclude_element_raises():
    """An unrecognised element name in exclude raises ValueError."""
    doc = Document()
    doc.load(text="# Hello\n\ntext\n")
    with pytest.raises(ValueError, match="Unknown element name"):
        validate(doc, {"allowed": False, "exclude": ["bogus_element"]})


def test_non_string_exclude_entry_raises():
    """A non-string entry in exclude raises ValueError."""
    doc = Document()
    doc.load(text="# Hello\n\ntext\n")
    with pytest.raises(ValueError):
        validate(doc, {"allowed": False, "exclude": [42]})


# ===================================================================
#  Empty document / no sections
# ===================================================================


def test_ascii_only_document_no_violations():
    """An all-ASCII document produces no violations under either setting."""
    doc = Document()
    doc.load(text="# Hello\n\nplain ASCII text only\n")
    assert validate(doc, {"allowed": False}) == []
    assert validate(doc, {"allowed": True}) == []


# ===================================================================
#  Rule discovery
# ===================================================================


def test_rule_is_discovered_by_engine():
    """The unicode rule is discovered and runnable via the engine."""
    from tiredize.linter.engine import run_linter
    doc = Document()
    doc.load(text="# Hello\n\ncafé\n")
    results = run_linter(doc, {"unicode": {"allowed": False}})
    assert len(results) == 1
    assert results[0].rule_id == "unicode"
