"""Tests for tiredize/linter/rules/line_length.py.

The engine tests already cover the basic happy path. This file adds
the CRLF and unicode coverage gaps identified in the audit.
"""

import copy

from tiredize.linter.rules.line_length import validate
from tiredize.markdown.types.document import Document


# ===================================================================
#  CRLF line endings
# ===================================================================


def test_crlf_excluded_from_length():
    r"""Line length is measured on content only, excluding \r\n."""
    # "# CRLF\r\n" content is "# CRLF" = 6 chars
    # With max 10, this should not violate
    doc = Document()
    doc.load(text="# CRLF\r\nshort\r\n")
    results = validate(doc, {"maximum_length": 10})
    assert results == []


def test_crlf_long_line_measured_without_endings():
    r"""A line that exceeds the limit even without \r\n is caught."""
    # "# Overly long header\r\n" content is 20 chars
    doc = Document()
    doc.load(text="# Overly long header\r\n")
    results = validate(doc, {"maximum_length": 10})
    assert len(results) == 1
    assert results[0].position.length == 10  # 20 - 10 overflow


def test_crlf_not_counted_as_length():
    r"""A line exactly at the limit with \r\n should not violate."""
    # "1234567890\r\n" content is 10 chars, limit is 10 -> no violation
    doc = Document()
    doc.load(text="# H\n1234567890\r\n")
    results = validate(doc, {"maximum_length": 10})
    assert results == []


# ===================================================================
#  Unicode / multi-byte characters (audit point 9)
# ===================================================================


def test_multibyte_characters_measured_in_chars():
    """Line length counts characters, not bytes."""
    # "\u00e9" is 1 char but 2 bytes in UTF-8
    # "# caf" + 5x e-acute + "\n" = 10 chars
    doc = Document()
    doc.load(text="# caf\u00e9\u00e9\u00e9\u00e9\u00e9\n")
    results = validate(doc, {"maximum_length": 10})
    assert results == []


def test_emoji_measured_in_chars():
    """Emoji are single characters for length purposes."""
    # "# \U0001f525\U0001f525\U0001f525\n" = 5 chars (# space fire fire fire)
    doc = Document()
    doc.load(text="# \U0001f525\U0001f525\U0001f525\n")
    results = validate(doc, {"maximum_length": 5})
    assert results == []


def test_multibyte_line_exceeds_limit():
    """A line with multi-byte chars that exceeds the limit is reported."""
    # "# caf\u00e9\u00e9\u00e9\u00e9\u00e9\u00e9\n" = 11 chars, limit 10
    doc = Document()
    doc.load(text="# caf\u00e9\u00e9\u00e9\u00e9\u00e9\u00e9\n")
    results = validate(doc, {"maximum_length": 10})
    assert len(results) == 1
    assert results[0].position.length == 1


# ===================================================================
#  Idempotency (audit point 7)
# ===================================================================


def test_validate_idempotent():
    """Running validate twice yields identical results."""
    doc = Document()
    doc.load(text="# This line is definitely too long for a limit of ten\n")
    config = {"maximum_length": 10}
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
    doc.load(text="# Guard\nsome content here\n")
    original_string = doc.string
    validate(doc, {"maximum_length": 10})
    assert doc.string == original_string


def test_validate_does_not_mutate_config():
    """validate() must not change the config dict."""
    doc = Document()
    doc.load(text="# Config test\n")
    config = {"maximum_length": 80}
    config_copy = copy.deepcopy(config)
    validate(doc, config)
    assert config == config_copy
