"""Tests for tiredize/linter/rules/links.py.

Covers config gating, each link type (valid/invalid), multiple link
types in same section, config passthrough, cross-component interactions,
unicode URLs, idempotency, state mutation, and partial failure.

All tests mock check_url_valid to isolate the rule's branching logic
from HTTP internals.
"""

import copy
from unittest.mock import patch

from tiredize.linter.rules.links import validate
from tiredize.markdown.types.document import Document


MOCK_TARGET = "tiredize.linter.rules.links.check_url_valid"


# ===================================================================
#  Config gating
# ===================================================================


def test_validate_false_returns_empty():
    """When config 'validate' is False, no links are checked."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    results = validate(doc, {"validate": False})
    assert results == []


def test_validate_missing_returns_empty():
    """When config has no 'validate' key, no links are checked."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    results = validate(doc, {})
    assert results == []


def test_validate_true_no_links():
    """When validate is True but document has no links, returns empty."""
    doc = Document()
    doc.load(text="# Just a heading\n\nNo links here.\n")
    with patch(MOCK_TARGET) as mock_check:
        results = validate(doc, {"validate": True})
    assert results == []
    mock_check.assert_not_called()


# ===================================================================
#  Inline link -- valid and invalid
# ===================================================================


def test_inline_link_valid():
    """Valid inline link produces no violation."""
    doc = Document()
    doc.load(text="# Nav\n[home](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        results = validate(doc, {"validate": True})
    assert results == []
    assert mock_check.call_count == 1


def test_inline_link_invalid():
    """Invalid inline link produces a violation with the URL in the message."""
    doc = Document()
    doc.load(text="# Nav\n[home](https://broken.example)\n")
    with patch(MOCK_TARGET, return_value=(False, 404, "not found")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Inline link" in results[0].message
    assert "https://broken.example" in results[0].message
    assert "404" in results[0].message


# ===================================================================
#  Bracket link -- valid and invalid
# ===================================================================


def test_bracket_link_valid():
    """Valid bracket link produces no violation."""
    doc = Document()
    doc.load(text="# Nav\n<https://example.com>\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        results = validate(doc, {"validate": True})
    assert results == []


def test_bracket_link_invalid():
    """Invalid bracket link produces a violation."""
    doc = Document()
    doc.load(text="# Nav\n<https://dead.example>\n")
    with patch(MOCK_TARGET, return_value=(False, 500, "server error")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Bracket link" in results[0].message
    assert "https://dead.example" in results[0].message


# ===================================================================
#  Bare link -- valid and invalid
# ===================================================================


def test_bare_link_valid():
    """Valid bare link produces no violation."""
    doc = Document()
    doc.load(text="# Nav\nhttps://example.com\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        results = validate(doc, {"validate": True})
    assert results == []


def test_bare_link_invalid():
    """Invalid bare link produces a violation."""
    doc = Document()
    doc.load(text="# Nav\nhttps://gone.example\n")
    with patch(MOCK_TARGET, return_value=(False, None, "timeout")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Bare link" in results[0].message
    assert "https://gone.example" in results[0].message


# ===================================================================
#  Reference definition -- valid and invalid
# ===================================================================


def test_reference_definition_valid():
    """Valid reference definition produces no violation."""
    doc = Document()
    doc.load(text="# Nav\n[ref]: https://example.com/page.html\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        results = validate(doc, {"validate": True})
    assert results == []


def test_reference_definition_invalid():
    """Invalid reference definition produces a violation."""
    doc = Document()
    doc.load(text="# Nav\n[ref]: https://missing.example/page.html\n")
    with patch(MOCK_TARGET, return_value=(False, 404, "not found")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Reference link" in results[0].message


# ===================================================================
#  Multiple link types in same section
# ===================================================================


def test_multiple_link_types_all_checked():
    """All link types in one section are checked."""
    md = (
        "# Kitchen Sink\n"
        "[inline](https://a.example/page.html)\n"
        "<https://b.example>\n"
        "https://c.example/path.html\n"
        "[ref]: https://d.example/ref.html\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        results = validate(doc, {"validate": True})
    assert results == []
    # All four links should have been checked
    assert mock_check.call_count >= 4


# ===================================================================
#  Config passthrough (timeout, headers)
# ===================================================================


def test_timeout_passed_to_check_url_valid():
    """The configured timeout is forwarded to check_url_valid."""
    doc = Document()
    doc.load(text="# Links\n[t](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True, "timeout": 42})
    _, kwargs = mock_check.call_args
    assert kwargs["timeout"] == 42


def test_headers_passed_to_check_url_valid():
    """The configured headers dict is forwarded to check_url_valid."""
    headers = {"Authorization": "Bearer secret-squirrel"}
    doc = Document()
    doc.load(text="# Links\n[h](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True, "headers": headers})
    _, kwargs = mock_check.call_args
    assert kwargs["headers"] == headers


def test_missing_timeout_passes_none():
    """When timeout is not in config, None is passed to check_url_valid."""
    doc = Document()
    doc.load(text="# Links\n[n](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True})
    _, kwargs = mock_check.call_args
    assert kwargs["timeout"] is None


def test_missing_headers_passes_none():
    """When headers is not in config, None is passed to check_url_valid."""
    doc = Document()
    doc.load(text="# Links\n[n](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True})
    _, kwargs = mock_check.call_args
    assert kwargs["headers"] is None


# ===================================================================
#  Cross-component interactions (audit point 5)
# ===================================================================


def test_same_url_inline_and_bare_both_checked():
    """Same URL as InlineLink and BareLink are both checked independently."""
    md = (
        "# Dupes\n"
        "[click](https://example.com/path.html)\n"
        "https://example.com/path.html\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(MOCK_TARGET, return_value=(False, 404, "gone")) as mock_check:
        results = validate(doc, {"validate": True})
    # Both link occurrences should produce violations
    assert len(results) >= 2
    assert mock_check.call_count >= 2


def test_multiple_sections_all_iterated():
    """Links in different sections are all checked, not just the first."""
    md = (
        "# Section One\n"
        "[a](https://alpha.example)\n"
        "# Section Two\n"
        "[b](https://beta.example)\n"
        "# Section Three\n"
        "[c](https://gamma.example)\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        results = validate(doc, {"validate": True})
    assert results == []
    assert mock_check.call_count == 3


# ===================================================================
#  Unicode URL (audit point 9)
# ===================================================================


def test_unicode_url_reaches_check_url_valid():
    """A link with unicode in the URL passes the URL intact."""
    doc = Document()
    doc.load(text="# Unicode\n[\u00e9dit](https://example.com/caf\u00e9)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True})
    _, kwargs = mock_check.call_args
    assert "caf\u00e9" in kwargs["url"]


# ===================================================================
#  Partial failure (audit point 10)
# ===================================================================


def test_exception_on_middle_link_crashes_rule():
    """An unexpected exception on link 2 of 3 is not swallowed.

    The links rule does not wrap check_url_valid in try/except, so an
    unexpected exception propagates. This documents actual behavior:
    the rule crashes and link 3 is NOT checked.
    """
    md = (
        "# Fragile\n"
        "[a](https://one.example)\n"
        "[b](https://two.example)\n"
        "[c](https://three.example)\n"
    )
    doc = Document()
    doc.load(text=md)
    call_count = 0

    def side_effect(document, url, timeout=None, headers=None):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("unexpected kaboom")
        return True, 200, None

    with patch(MOCK_TARGET, side_effect=side_effect):
        try:
            validate(doc, {"validate": True})
            crashed = False
        except RuntimeError:
            crashed = True
    # Document: the rule does not catch unexpected exceptions
    assert crashed, "Expected the rule to propagate the exception"


# ===================================================================
#  Idempotency (audit point 7)
# ===================================================================


def test_validate_idempotent():
    """Running validate twice yields identical results."""
    doc = Document()
    doc.load(text="# Repeat\n[go](https://example.com)\n")
    config = {"validate": True}
    with patch(MOCK_TARGET, return_value=(False, 503, "unavailable")):
        first = validate(doc, config)
    with patch(MOCK_TARGET, return_value=(False, 503, "unavailable")):
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
    doc.load(text="# Safe\n[x](https://example.com)\n")
    original_string = doc.string
    original_sections = len(doc.sections)
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        validate(doc, {"validate": True})
    assert doc.string == original_string
    assert len(doc.sections) == original_sections


def test_validate_does_not_mutate_config():
    """validate() must not change the config dict."""
    doc = Document()
    doc.load(text="# Lock\n[x](https://example.com)\n")
    config = {"validate": True, "timeout": 10}
    config_copy = copy.deepcopy(config)
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        validate(doc, config)
    assert config == config_copy
