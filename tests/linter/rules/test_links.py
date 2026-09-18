"""Tests for tiredize/linter/rules/links.py.

Covers config gating, each link type (valid/invalid), multiple link
types in same section, config passthrough, cross-component interactions,
unicode URLs, idempotency, state mutation, and partial failure.

All tests mock check_url_valid to isolate the rule's branching logic
from HTTP internals.
"""

import copy
from unittest.mock import patch

import pytest

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


# ===================================================================
#  Configuration validation (key level)
#
#  `validate` is required: without it the rule checks no links, so
#  enabling `links` would be a no-op. Present-but-false is legal and
#  deliberately disables URL checking. See "Validating rule
#  configuration" in .context/issues/main-module-exit-code.md.
# ===================================================================


def test_validate_missing_raises():
    """Enabling the rule without `validate` would check nothing."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {})
    message = str(excinfo.value)
    assert "links" in message
    assert "validate" in message


def test_unknown_key_raises():
    """A key the rule does not accept is an error."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {"validate": False, "snooze_button": True})
    message = str(excinfo.value)
    assert "links" in message
    assert "snooze_button" in message


def test_validate_wrong_type_raises():
    """`validate` wants a boolean, not a string."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError, match="validate"):
        validate(doc, {"validate": "yes please"})


def test_timeout_wrong_type_raises():
    """An optional key is still type-checked."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError, match="timeout"):
        validate(doc, {"validate": True, "timeout": "a while"})


def test_unknown_key_reported_before_bad_status_code():
    """Key-level validation runs before the value-level check."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {
            "validate": True,
            "valid_status_codes": ["ok"],
            "snooze_button": True,
        })
    assert "snooze_button" in str(excinfo.value)


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
#  Autolink -- valid and invalid
# ===================================================================


def test_autolink_valid():
    """Valid autolink produces no violation."""
    doc = Document()
    doc.load(text="# Nav\n<https://example.com>\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        results = validate(doc, {"validate": True})
    assert results == []


def test_autolink_invalid():
    """Invalid autolink produces a violation."""
    doc = Document()
    doc.load(text="# Nav\n<https://dead.example>\n")
    with patch(MOCK_TARGET, return_value=(False, 500, "server error")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Autolink" in results[0].message
    assert "https://dead.example" in results[0].message


# ===================================================================
#  Extended autolink -- valid and invalid
# ===================================================================


def test_extended_autolink_valid():
    """Valid extended autolink produces no violation."""
    doc = Document()
    doc.load(text="# Nav\nhttps://example.com\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)):
        results = validate(doc, {"validate": True})
    assert results == []


def test_extended_autolink_invalid():
    """Invalid extended autolink produces a violation."""
    doc = Document()
    doc.load(text="# Nav\nhttps://gone.example\n")
    with patch(MOCK_TARGET, return_value=(False, None, "timeout")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Extended autolink" in results[0].message
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


def test_valid_status_codes_passed_to_check_url_valid():
    """The configured valid_status_codes list is forwarded to
    check_url_valid."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True, "valid_status_codes": [200, 404]})
    _, kwargs = mock_check.call_args
    assert kwargs["valid_status_codes"] == [200, 404]


def test_missing_valid_status_codes_passes_none():
    """When valid_status_codes is absent, None is passed to check_url_valid."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True})
    _, kwargs = mock_check.call_args
    assert kwargs["valid_status_codes"] is None


def test_valid_status_codes_wildcard_accepted():
    """A wildcard entry like '2xx' is forwarded without error."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {"validate": True, "valid_status_codes": ["2xx", "3xx"]})
    _, kwargs = mock_check.call_args
    assert kwargs["valid_status_codes"] == ["2xx", "3xx"]


def test_valid_status_codes_mixed_wildcard_and_int_accepted():
    """Wildcards and exact codes can be mixed."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {
            "validate": True,
            "valid_status_codes": ["2xx", 404],
        })
    _, kwargs = mock_check.call_args
    assert kwargs["valid_status_codes"] == ["2xx", 404]


def test_valid_status_codes_invalid_string_raises():
    """A string that is not a valid wildcard raises ValueError."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    import pytest
    with pytest.raises(ValueError, match="valid_status_codes"):
        validate(doc, {"validate": True, "valid_status_codes": ["ok"]})


def test_valid_status_codes_non_integer_raises():
    """A non-integer, non-wildcard entry raises ValueError."""
    doc = Document()
    doc.load(text="# Links\n[v](https://example.com)\n")
    import pytest
    with pytest.raises(ValueError, match="valid_status_codes"):
        validate(doc, {"validate": True, "valid_status_codes": [200, "ok"]})


# ===================================================================
#  Cross-component interactions (audit point 5)
# ===================================================================


def test_same_url_inline_and_extended_autolink_both_checked():
    """Same URL as InlineLink and ExtendedAutolink are both checked
    independently."""
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

    def side_effect(document, url, timeout=None, headers=None, **_):
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


# ===================================================================
#  exclude config option
# ===================================================================


def test_excluded_wildcard_domain_not_checked():
    """A URL whose hostname matches a wildcard pattern is not validated."""
    doc = Document()
    doc.load(text="# Links\n[x](https://github.mycompany.com/org/repo)\n")
    with patch(
        MOCK_TARGET, return_value=(False, 404, "unreachable")
    ) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com"],
        })
    assert results == []
    mock_check.assert_not_called()


def test_excluded_exact_domain_not_checked():
    """A URL whose hostname matches an exact pattern is not validated."""
    doc = Document()
    doc.load(text=(
        "# Links\n[x](https://mycompany.atlassian.net/browse/PROJ-1)\n"
    ))
    with patch(
        MOCK_TARGET, return_value=(False, 404, "unreachable")
    ) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["mycompany.atlassian.net"],
        })
    assert results == []
    mock_check.assert_not_called()


def test_non_excluded_domain_still_checked():
    """A URL whose hostname matches no pattern is still validated."""
    doc = Document()
    doc.load(text="# Links\n[x](https://external.example.com/page)\n")
    with patch(
        MOCK_TARGET, return_value=(False, 404, "not found")
    ) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com"],
        })
    assert len(results) == 1
    mock_check.assert_called_once()


def test_exclude_mixed_document():
    """Excluded links are skipped; non-excluded links are still checked."""
    md = (
        "# Links\n"
        "[internal](https://github.mycompany.com/org/repo)\n"
        "[external](https://example.com)\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com"],
        })
    assert results == []
    assert mock_check.call_count == 1


def test_empty_exclude_validates_all():
    """An empty exclude list leaves all links subject to validation."""
    doc = Document()
    doc.load(text="# Links\n[x](https://mycompany.com/page.html)\n")
    with patch(
        MOCK_TARGET, return_value=(False, 404, "not found")
    ) as mock_check:
        results = validate(doc, {"validate": True, "exclude": []})
    assert len(results) == 1
    mock_check.assert_called_once()


def test_multiple_exclude_patterns():
    """Multiple exclude patterns are each applied."""
    md = (
        "# Links\n"
        "[a](https://github.mycompany.com/org/repo)\n"
        "[b](https://mycompany.atlassian.net/browse/PROJ-1)\n"
        "[c](https://external.example.com)\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock_check:
        validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com", "mycompany.atlassian.net"],
        })
    assert mock_check.call_count == 1


def test_exclude_applies_to_all_link_types():
    """Domain exclusions apply to inline links, autolinks, extended
    autolinks, and reference definitions."""
    md = (
        "# Links\n"
        "[inline](https://internal.mycompany.com/a)\n"
        "<https://internal.mycompany.com/b>\n"
        "https://internal.mycompany.com/c\n"
        "[ref]: https://internal.mycompany.com/d.html\n"
    )
    doc = Document()
    doc.load(text=md)
    with patch(
        MOCK_TARGET, return_value=(False, 404, "unreachable")
    ) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com"],
        })
    assert results == []
    mock_check.assert_not_called()


def test_relative_url_not_affected_by_domain_exclusion():
    """Relative URLs have no domain and are not excluded by domain patterns."""
    doc = Document()
    doc.load(text="# Links\n[ref]: ./some/path.md\n")
    with patch(
        MOCK_TARGET,
        return_value=(False, None, "relative file not found"),
    ) as mock_check:
        validate(doc, {
            "validate": True,
            "exclude": ["*.mycompany.com"],
        })
    mock_check.assert_called_once()


@pytest.mark.skip(
    reason="links-exclude-malformed-url-crash: _is_excluded raises on "
    "URLs urlparse cannot parse"
)
def test_malformed_url_with_exclude_configured_is_a_finding_not_a_crash():
    """A URL urlparse cannot parse (an unclosed IPv6 bracket) must be
    reported as a finding even when `exclude` is configured. Today
    `_is_excluded` calls `urlparse(url).hostname`, which raises
    `ValueError: Invalid IPv6 URL` before check_url_valid can report
    the failure as a tuple; without `exclude` the helper returns early
    and the same document is fine (see
    test_scheme_gate_does_not_raise_on_malformed_url). Verified to
    fail on 2026-09-18; unskip when the named issue lands."""
    doc = Document()
    doc.load(text="# Nav\n<http://[::1>\n")
    with patch(
        MOCK_TARGET, return_value=(False, None, "invalid url")
    ) as mock_check:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.example.com"],
        })
    mock_check.assert_called_once()
    assert len(results) == 1
    assert "http://[::1" in results[0].message


def test_non_string_exclude_entry_still_raises_value_level_error():
    """Key-level validation does not swallow the value-level check."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError, match="entries must be strings"):
        validate(doc, {"validate": True, "exclude": [42]})


def test_bool_status_code_still_raises_value_level_error():
    """`valid_status_codes` is a list, so its entries are checked."""
    doc = Document()
    doc.load(text="# Links\n[click](https://example.com)\n")
    with pytest.raises(ValueError, match="valid_status_codes"):
        validate(doc, {"validate": True, "valid_status_codes": [True]})


# ===================================================================
#  Scheme gating (white-box)
#
#  The rule hands a URL to check_url_valid only when it has no
#  scheme (anchors, relative paths, and anything else the helper
#  already reports on) or its scheme is http or https. The gate is
#  the same for every link kind, so an inline link or reference
#  definition with a mailto: target is skipped just like an autolink.
#  The acceptance tests further down cover the autolink forms.
# ===================================================================


@pytest.mark.parametrize(
    "markdown",
    [
        "[mail](mailto:crew@moonbase.example)",
        "[files](ftp://files.moonbase.example)",
        "[chat](irc://chat.moonbase.example/dock)",
        "[mail]: mailto:crew@moonbase.example",
        "[files]: ftp://files.moonbase.example",
    ],
    ids=["inline-mailto", "inline-ftp", "inline-irc", "ref-mailto", "ref-ftp"],
)
def test_non_http_scheme_skipped_for_inline_and_reference_links(markdown):
    doc = Document()
    doc.load(text=f"# Nav\n{markdown}\n")
    with patch(MOCK_TARGET, return_value=(False, None, "nope")) as mock:
        results = validate(doc, {"validate": True})
    assert results == []
    mock.assert_not_called()


@pytest.mark.parametrize(
    ("markdown", "url"),
    [
        ("[top](#nav)", "#nav"),
        ("[map](./treasure-map.md)", "./treasure-map.md"),
        ("[up](../index.md)", "../index.md"),
        ("[bare](moonbase.example/dock)", "moonbase.example/dock"),
        ("[nav]: #nav", "#nav"),
        ("[map]: ./treasure-map.md", "./treasure-map.md"),
    ],
    ids=["anchor", "dot-relative", "dot-dot-relative", "no-scheme",
         "ref-anchor", "ref-relative"],
)
def test_scheme_less_targets_still_reach_check_url_valid(markdown, url):
    """Anchors, relative paths and scheme-less URLs carry no scheme,
    so they are handed to check_url_valid exactly as before."""
    doc = Document()
    doc.load(text=f"# Nav\n{markdown}\n")
    with patch(MOCK_TARGET, return_value=(True, None, None)) as mock:
        validate(doc, {"validate": True})
    mock.assert_called_once()
    assert mock.call_args.kwargs["url"] == url


@pytest.mark.parametrize(
    ("markdown", "url"),
    [
        ("<HTTPS://moonbase.example>", "HTTPS://moonbase.example"),
        ("Http://moonbase.example", "Http://moonbase.example"),
        ("[x](HTTP://moonbase.example)", "HTTP://moonbase.example"),
    ],
    ids=["autolink", "extended", "inline"],
)
def test_upper_case_http_scheme_is_still_checked(markdown, url):
    doc = Document()
    doc.load(text=f"# Nav\n{markdown}\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock:
        validate(doc, {"validate": True})
    mock.assert_called_once()
    assert mock.call_args.kwargs["url"] == url


def test_scheme_gate_does_not_raise_on_malformed_url():
    """A URL urllib cannot parse (an unclosed IPv6 bracket) still goes
    to check_url_valid, which reports the failure as a tuple."""
    doc = Document()
    doc.load(text="# Nav\n<http://[::1>\n")
    with patch(
        MOCK_TARGET, return_value=(False, None, "invalid url")
    ) as mock:
        results = validate(doc, {"validate": True})
    mock.assert_called_once()
    assert len(results) == 1
    assert "http://[::1" in results[0].message


def test_scheme_gate_runs_before_exclusion():
    """A skipped scheme never reaches the hostname exclusion, whose
    urlparse would otherwise see the address as a path."""
    doc = Document()
    doc.load(text="# Nav\n<mailto:crew@moonbase.example>\n")
    with patch(MOCK_TARGET, return_value=(False, None, "nope")) as mock:
        results = validate(doc, {
            "validate": True,
            "exclude": ["*.moonbase.example"],
        })
    assert results == []
    mock.assert_not_called()


# ===================================================================
#  Acceptance tests: autolink-gfm-parity (step 2, before implementation)
#
#  The `links` rule validates only `http` and `https` targets. Every
#  other scheme the parser now recognises (`mailto:`, `xmpp:`,
#  `irc:`, `ftp:`, unregistered schemes) is a link for the parser but
#  produces no finding and no HTTP request. `www.` extended autolinks
#  are validated against `http://` + the matched text. Finding
#  messages name the element as "Autolink" or "Extended autolink".
#
#  `Section.autolinks` and `Section.autolinks_extended` do not exist
#  until step 3; the tests read them to prove the parser recognised
#  the link before asserting the rule stayed silent.
# ===================================================================


def _autolinks(doc):
    return [link for s in doc.sections for link in s.autolinks]


def _autolinks_extended(doc):
    return [link for s in doc.sections for link in s.autolinks_extended]


@pytest.mark.parametrize(
    ("markdown", "url"),
    [
        ("<irc://foo.bar:2233/baz>", "irc://foo.bar:2233/baz"),
        ("<ftp://files.example.com>", "ftp://files.example.com"),
        ("<a+b+c:d>", "a+b+c:d"),
        ("<localhost:5001/foo>", "localhost:5001/foo"),
        ("<foo@bar.example.com>", "mailto:foo@bar.example.com"),
        ("<MAILTO:FOO@BAR.BAZ>", "MAILTO:FOO@BAR.BAZ"),
    ],
    ids=["irc", "ftp", "unregistered", "localhost", "email", "MAILTO"],
)
def test_non_http_autolink_recognised_but_not_validated(markdown, url):
    """The parser sees the autolink; the rule neither checks it nor
    reports it."""
    doc = Document()
    doc.load(text=f"# Nav\n{markdown}\n")
    assert [link.url for link in _autolinks(doc)] == [url]
    with patch(MOCK_TARGET, return_value=(False, None, "nope")) as mock:
        results = validate(doc, {"validate": True})
    assert results == []
    mock.assert_not_called()


@pytest.mark.parametrize(
    ("markdown", "url"),
    [
        ("foo@bar.baz", "mailto:foo@bar.baz"),
        ("mailto:foo@bar.baz", "mailto:foo@bar.baz"),
        ("xmpp:foo@bar.baz/txt", "xmpp:foo@bar.baz/txt"),
    ],
    ids=["bare-email", "mailto", "xmpp"],
)
def test_non_http_extended_autolink_recognised_but_not_validated(
    markdown, url,
):
    """The parser sees the extended autolink; the rule neither checks
    it nor reports it."""
    doc = Document()
    doc.load(text=f"# Nav\n{markdown}\n")
    assert [link.url for link in _autolinks_extended(doc)] == [url]
    with patch(MOCK_TARGET, return_value=(False, None, "nope")) as mock:
        results = validate(doc, {"validate": True})
    assert results == []
    mock.assert_not_called()


def test_www_extended_autolink_validated_over_http():
    """A `www.` link is checked as `http://` + the matched text."""
    doc = Document()
    doc.load(text="# Nav\nVisit www.moonbase.example/dock today.\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock:
        results = validate(doc, {"validate": True})
    assert results == []
    mock.assert_called_once()
    _, kwargs = mock.call_args
    assert kwargs["url"] == "http://www.moonbase.example/dock"


def test_www_extended_autolink_finding_names_http_url():
    doc = Document()
    doc.load(text="# Nav\nVisit www.moonbase.example/dock today.\n")
    with patch(MOCK_TARGET, return_value=(False, 404, "not found")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Extended autolink" in results[0].message
    assert "http://www.moonbase.example/dock" in results[0].message
    assert "404" in results[0].message


def test_www_extended_autolink_excluded_by_hostname():
    """`exclude` matches the hostname of the normalised target."""
    doc = Document()
    doc.load(text="# Nav\nVisit www.moonbase.example/dock today.\n")
    assert [link.url for link in _autolinks_extended(doc)] == [
        "http://www.moonbase.example/dock",
    ]
    with patch(MOCK_TARGET, return_value=(False, 404, "gone")) as mock:
        results = validate(doc, {
            "validate": True,
            "exclude": ["www.moonbase.example"],
        })
    assert results == []
    mock.assert_not_called()


def test_autolink_finding_names_element_autolink():
    doc = Document()
    doc.load(text="# Nav\n<https://dead.example>\n")
    with patch(MOCK_TARGET, return_value=(False, 500, "server error")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Autolink" in results[0].message
    assert "Extended" not in results[0].message
    assert "https://dead.example" in results[0].message


def test_extended_autolink_finding_names_element_extended_autolink():
    doc = Document()
    doc.load(text="# Nav\nhttps://gone.example\n")
    with patch(MOCK_TARGET, return_value=(False, None, "timeout")):
        results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Extended autolink" in results[0].message
    assert "https://gone.example" in results[0].message


def test_extended_autolink_validated_without_trailing_punctuation():
    """The URL handed to check_url_valid is the trimmed match."""
    doc = Document()
    doc.load(text="# Nav\nRead https://moonbase.example/docs.\n")
    with patch(MOCK_TARGET, return_value=(True, 200, None)) as mock:
        validate(doc, {"validate": True})
    _, kwargs = mock.call_args
    assert kwargs["url"] == "https://moonbase.example/docs"


@pytest.mark.parametrize(
    "line",
    [
        "Run ./configure before you summon make.",
        "The ritual is described in ../guide.md and nowhere else.",
        r"Delete every \*.dll in the goblin cache.",
        r"Mount \\server\share before the raid.",
    ],
    ids=["dot-slash", "dot-dot-slash", "star-dll", "unc-path"],
)
def test_prose_paths_and_escapes_produce_no_finding(line):
    """The false positives that opened the issue, end to end: prose
    that GitHub renders as text must not be reported as a link."""
    doc = Document()
    doc.load(text=f"# Rituals\n{line}\n")
    with patch(MOCK_TARGET, return_value=(False, None, "nope")) as mock:
        results = validate(doc, {"validate": True})
    assert results == []
    mock.assert_not_called()


# ===================================================================
#  Relative path validation through inline links and reference
#  definitions is unchanged. These pass today and stay unskipped:
#  they guard the validation the issue keeps while removing `./`
#  matching from extended autolinks. check_url_valid is not mocked
#  because relative paths never reach HTTP.
# ===================================================================


def test_inline_link_relative_path_found(tmp_path):
    doc_file = tmp_path / "grimoire.md"
    doc_file.write_text(
        "# Rituals\nSee [the map](./treasure-map.md) first.\n",
        encoding="utf-8",
    )
    (tmp_path / "treasure-map.md").write_text("# X marks", encoding="utf-8")
    doc = Document()
    doc.load(path=doc_file)
    assert validate(doc, {"validate": True}) == []


def test_inline_link_relative_path_missing(tmp_path):
    doc_file = tmp_path / "grimoire.md"
    doc_file.write_text(
        "# Rituals\nSee [the map](./treasure-map.md) first.\n",
        encoding="utf-8",
    )
    doc = Document()
    doc.load(path=doc_file)
    results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Inline link" in results[0].message
    assert "./treasure-map.md" in results[0].message
    assert "relative file not found" in results[0].message


def test_reference_definition_relative_path_found(tmp_path):
    doc_file = tmp_path / "grimoire.md"
    doc_file.write_text(
        "# Rituals\n[map]: ./treasure-map.md\n",
        encoding="utf-8",
    )
    (tmp_path / "treasure-map.md").write_text("# X marks", encoding="utf-8")
    doc = Document()
    doc.load(path=doc_file)
    assert validate(doc, {"validate": True}) == []


def test_reference_definition_relative_path_missing(tmp_path):
    doc_file = tmp_path / "grimoire.md"
    doc_file.write_text(
        "# Rituals\n[map]: ./treasure-map.md\n",
        encoding="utf-8",
    )
    doc = Document()
    doc.load(path=doc_file)
    results = validate(doc, {"validate": True})
    assert len(results) == 1
    assert "Reference link" in results[0].message
    assert "./treasure-map.md" in results[0].message
    assert "relative file not found" in results[0].message
