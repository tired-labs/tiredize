"""Acceptance tests for GFM autolink parity in tiredize/markdown/types/link.py.

Black-box tests written at step 2 of issue `autolink-gfm-parity`,
before implementation. They exercise the Public Contract for
`Autolink` (GFM 0.29-gfm section 6.8, Autolinks) and
`ExtendedAutolink` (section 6.9, Autolinks (extension)).

The 33 conformance cases are the specification's own examples,
numbered as published at https://github.github.com/gfm/ (603-635).
Each example test carries its number so a reader can check it
against the specification without trusting the test author. The
markdown input is transcribed verbatim; the expected result is the
link GitHub would render, expressed as tiredize sees it: `string`
is the visible link text and `url` is the href.

tiredize is a parser, not a renderer, so nothing here asserts on
rendered HTML. Where an example has several input paragraphs, every
paragraph is asserted.

The names `Autolink` and `ExtendedAutolink` do not exist until step 3.
They are imported inside the helpers below rather than at module
level so that collection succeeds and every test fails on its own,
with a reason that names the missing class.
"""

# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position


PENDING = "autolink-gfm-parity: awaiting implementation (step 3)"


# ===================================================================
#  Helpers
#
#  Both helpers return the extracted links as (string, url) pairs so
#  that each test states the exact set of links the contract
#  promises and nothing else.
# ===================================================================


def autolinks(text: str) -> list[tuple[str, str]]:
    """Run `Autolink.extract` and return (string, url) pairs."""
    from tiredize.markdown.types.link import Autolink
    return [(link.string, link.url) for link in Autolink.extract(text)]


def extended_autolinks(text: str) -> list[tuple[str, str]]:
    """Run `ExtendedAutolink.extract` and return (string, url) pairs."""
    from tiredize.markdown.types.link import ExtendedAutolink
    return [
        (link.string, link.url)
        for link in ExtendedAutolink.extract(text)
    ]


# ===================================================================
#  GFM 6.8 Autolinks -- URI autolinks (examples 603-612)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_603_http_uri():
    text = "<http://foo.bar.baz>"
    assert autolinks(text) == [
        ("<http://foo.bar.baz>", "http://foo.bar.baz"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_604_query_string_kept_as_written():
    text = "<http://foo.bar.baz/test?q=hello&id=22&boolean>"
    assert autolinks(text) == [
        (
            "<http://foo.bar.baz/test?q=hello&id=22&boolean>",
            "http://foo.bar.baz/test?q=hello&id=22&boolean",
        ),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_605_irc_scheme():
    text = "<irc://foo.bar:2233/baz>"
    assert autolinks(text) == [
        ("<irc://foo.bar:2233/baz>", "irc://foo.bar:2233/baz"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_606_uppercase_scheme_is_a_uri_not_an_email():
    """`MAILTO:` is a scheme here, so the href is the URI as written
    -- no second `mailto:` is prepended."""
    text = "<MAILTO:FOO@BAR.BAZ>"
    assert autolinks(text) == [
        ("<MAILTO:FOO@BAR.BAZ>", "MAILTO:FOO@BAR.BAZ"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_607_unregistered_scheme_with_plus_signs():
    text = "<a+b+c:d>"
    assert autolinks(text) == [("<a+b+c:d>", "a+b+c:d")]


@pytest.mark.skip(reason=PENDING)
def test_example_608_made_up_scheme_with_comma():
    text = "<made-up-scheme://foo,bar>"
    assert autolinks(text) == [
        ("<made-up-scheme://foo,bar>", "made-up-scheme://foo,bar"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_609_dot_dot_is_a_valid_uri_inside_brackets():
    text = "<http://../>"
    assert autolinks(text) == [("<http://../>", "http://../")]


@pytest.mark.skip(reason=PENDING)
def test_example_610_localhost_scheme_with_port():
    text = "<localhost:5001/foo>"
    assert autolinks(text) == [
        ("<localhost:5001/foo>", "localhost:5001/foo"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_611_space_inside_brackets_is_not_an_autolink():
    text = "<http://foo.bar/baz bim>"
    assert autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
def test_example_612_backslashes_are_literal_inside_brackets():
    """The href in the spec is percent-encoded by the renderer; the
    parser reports the URI as written in the source."""
    text = "<http://example.com/\\[\\>"
    assert autolinks(text) == [
        ("<http://example.com/\\[\\>", "http://example.com/\\[\\"),
    ]


# ===================================================================
#  GFM 6.8 Autolinks -- email autolinks (examples 613-615)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_613_email_autolink_gets_mailto_href():
    text = "<foo@bar.example.com>"
    assert autolinks(text) == [
        ("<foo@bar.example.com>", "mailto:foo@bar.example.com"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_614_email_with_plus_and_mixed_case_domain():
    text = "<foo+special@Bar.baz-bar0.com>"
    assert autolinks(text) == [
        (
            "<foo+special@Bar.baz-bar0.com>",
            "mailto:foo+special@Bar.baz-bar0.com",
        ),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_615_backslash_in_email_is_not_an_escape():
    text = r"<foo\+@bar.example.com>"
    assert autolinks(text) == []


# ===================================================================
#  GFM 6.8 Autolinks -- these are not autolinks (examples 616-621)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_616_empty_brackets():
    text = "<>"
    assert autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
def test_example_617_spaces_around_uri_inside_brackets():
    text = "< http://foo.bar >"
    assert autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
def test_example_618_one_character_scheme_is_too_short():
    text = "<m:abc>"
    assert autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
def test_example_619_no_scheme_and_no_at_sign():
    text = "<foo.bar.baz>"
    assert autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
def test_example_620_bare_uri_is_not_an_autolink_but_is_extended():
    """Without brackets this is not a section 6.8 autolink. Under the
    section 6.9 extension it is an extended autolink (see 629)."""
    text = "http://example.com"
    assert autolinks(text) == []
    assert extended_autolinks(text) == [
        ("http://example.com", "http://example.com"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_621_bare_email_is_not_an_autolink_but_is_extended():
    """Without brackets this is not a section 6.8 autolink. Under the
    section 6.9 extension it is an extended autolink (see 630)."""
    text = "foo@bar.example.com"
    assert autolinks(text) == []
    assert extended_autolinks(text) == [
        ("foo@bar.example.com", "mailto:foo@bar.example.com"),
    ]


# ===================================================================
#  GFM 6.9 Autolinks (extension) -- www autolinks (examples 622-628)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_622_www_autolink_gets_http_inserted():
    text = "www.commonmark.org"
    assert extended_autolinks(text) == [
        ("www.commonmark.org", "http://www.commonmark.org"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_623_www_autolink_with_path_in_prose():
    text = "Visit www.commonmark.org/help for more information."
    assert extended_autolinks(text) == [
        ("www.commonmark.org/help", "http://www.commonmark.org/help"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_624_trailing_period_excluded():
    """Trailing punctuation is not part of the link, though the same
    characters may appear inside it (`a.b`)."""
    assert extended_autolinks("Visit www.commonmark.org.") == [
        ("www.commonmark.org", "http://www.commonmark.org"),
    ]
    assert extended_autolinks("Visit www.commonmark.org/a.b.") == [
        ("www.commonmark.org/a.b", "http://www.commonmark.org/a.b"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_625_unmatched_trailing_parentheses_excluded():
    link = "www.google.com/search?q=Markup+(business)"
    href = "http://" + link
    assert extended_autolinks(
        "www.google.com/search?q=Markup+(business)"
    ) == [(link, href)]
    assert extended_autolinks(
        "www.google.com/search?q=Markup+(business)))"
    ) == [(link, href)]
    assert extended_autolinks(
        "(www.google.com/search?q=Markup+(business))"
    ) == [(link, href)]
    assert extended_autolinks(
        "(www.google.com/search?q=Markup+(business)"
    ) == [(link, href)]


@pytest.mark.skip(reason=PENDING)
def test_example_626_parenthesis_check_only_when_link_ends_in_paren():
    text = "www.google.com/search?q=(business))+ok"
    assert extended_autolinks(text) == [
        (
            "www.google.com/search?q=(business))+ok",
            "http://www.google.com/search?q=(business))+ok",
        ),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_627_entity_like_tail_excluded():
    assert extended_autolinks(
        "www.google.com/search?q=commonmark&hl=en"
    ) == [
        (
            "www.google.com/search?q=commonmark&hl=en",
            "http://www.google.com/search?q=commonmark&hl=en",
        ),
    ]
    assert extended_autolinks(
        "www.google.com/search?q=commonmark&hl;"
    ) == [
        (
            "www.google.com/search?q=commonmark",
            "http://www.google.com/search?q=commonmark",
        ),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_628_less_than_ends_the_link():
    text = "www.commonmark.org/he<lp"
    assert extended_autolinks(text) == [
        ("www.commonmark.org/he", "http://www.commonmark.org/he"),
    ]


# ===================================================================
#  GFM 6.9 Autolinks (extension) -- url autolinks (example 629)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_629_http_and_https_url_autolinks():
    assert extended_autolinks("http://commonmark.org") == [
        ("http://commonmark.org", "http://commonmark.org"),
    ]
    assert extended_autolinks(
        "(Visit https://encrypted.google.com/search?q=Markup+(business))"
    ) == [
        (
            "https://encrypted.google.com/search?q=Markup+(business)",
            "https://encrypted.google.com/search?q=Markup+(business)",
        ),
    ]


# ===================================================================
#  GFM 6.9 Autolinks (extension) -- email autolinks (examples 630-632)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_630_email_autolink_gets_mailto_inserted():
    text = "foo@bar.baz"
    assert extended_autolinks(text) == [
        ("foo@bar.baz", "mailto:foo@bar.baz"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_631_plus_allowed_before_at_sign_but_not_after():
    text = (
        "hello@mail+xyz.example isn't valid, "
        "but hello+xyz@mail.example is."
    )
    assert extended_autolinks(text) == [
        ("hello+xyz@mail.example", "mailto:hello+xyz@mail.example"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_632_email_trailing_characters():
    """A trailing `.` is excluded from the address; a trailing `-` or
    `_` means the whole thing is not an email address."""
    assert extended_autolinks("a.b-c_d@a.b") == [
        ("a.b-c_d@a.b", "mailto:a.b-c_d@a.b"),
    ]
    assert extended_autolinks("a.b-c_d@a.b.") == [
        ("a.b-c_d@a.b", "mailto:a.b-c_d@a.b"),
    ]
    assert extended_autolinks("a.b-c_d@a.b-") == []
    assert extended_autolinks("a.b-c_d@a.b_") == []


# ===================================================================
#  GFM 6.9 Autolinks (extension) -- protocol autolinks (633-635)
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_example_633_mailto_and_xmpp_protocol_autolinks():
    """The scheme is part of the matched text, so `string` and `url`
    are identical for protocol autolinks."""
    assert extended_autolinks("mailto:foo@bar.baz") == [
        ("mailto:foo@bar.baz", "mailto:foo@bar.baz"),
    ]
    assert extended_autolinks("mailto:a.b-c_d@a.b") == [
        ("mailto:a.b-c_d@a.b", "mailto:a.b-c_d@a.b"),
    ]
    assert extended_autolinks("mailto:a.b-c_d@a.b.") == [
        ("mailto:a.b-c_d@a.b", "mailto:a.b-c_d@a.b"),
    ]
    assert extended_autolinks("mailto:a.b-c_d@a.b/") == [
        ("mailto:a.b-c_d@a.b", "mailto:a.b-c_d@a.b"),
    ]
    assert extended_autolinks("mailto:a.b-c_d@a.b-") == []
    assert extended_autolinks("mailto:a.b-c_d@a.b_") == []
    assert extended_autolinks("xmpp:foo@bar.baz") == [
        ("xmpp:foo@bar.baz", "xmpp:foo@bar.baz"),
    ]
    assert extended_autolinks("xmpp:foo@bar.baz.") == [
        ("xmpp:foo@bar.baz", "xmpp:foo@bar.baz"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_634_xmpp_resource_after_slash():
    assert extended_autolinks("xmpp:foo@bar.baz/txt") == [
        ("xmpp:foo@bar.baz/txt", "xmpp:foo@bar.baz/txt"),
    ]
    assert extended_autolinks("xmpp:foo@bar.baz/txt@bin") == [
        ("xmpp:foo@bar.baz/txt@bin", "xmpp:foo@bar.baz/txt@bin"),
    ]
    assert extended_autolinks("xmpp:foo@bar.baz/txt@bin.com") == [
        ("xmpp:foo@bar.baz/txt@bin.com", "xmpp:foo@bar.baz/txt@bin.com"),
    ]


@pytest.mark.skip(reason=PENDING)
def test_example_635_second_slash_ends_xmpp_resource():
    text = "xmpp:foo@bar.baz/txt/bin"
    assert extended_autolinks(text) == [
        ("xmpp:foo@bar.baz/txt", "xmpp:foo@bar.baz/txt"),
    ]


# ===================================================================
#  Preceding-character rule, beyond the specification examples
#
#  An extended autolink is recognised only at the start of the text,
#  after whitespace, or after one of `*`, `_`, `~`, `(`. The same
#  URL directly after a letter, a digit, or `"` is plain text.
# ===================================================================


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize("delimiter", ["*", "_", "~", "("])
@pytest.mark.parametrize(
    ("link", "href"),
    [
        ("www.moonbase.example", "http://www.moonbase.example"),
        ("https://moonbase.example", "https://moonbase.example"),
    ],
)
def test_extended_autolink_matches_after_delimiter(delimiter, link, href):
    text = f"launch {delimiter}{link} tonight"
    assert extended_autolinks(text) == [(link, href)]


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize("preceding", ["x", "7", '"'])
@pytest.mark.parametrize(
    "link",
    ["www.moonbase.example", "https://moonbase.example"],
)
def test_extended_autolink_not_matched_after_letter_digit_or_quote(
    preceding, link,
):
    text = f"launch {preceding}{link} tonight"
    assert extended_autolinks(text) == []


# ===================================================================
#  Escape sequences and relative paths are plain text
#
#  These are the cases that opened the issue: backslash escapes and
#  `./` paths in prose were extracted and reported as unreachable
#  links. GFM renders every one of them as text.
# ===================================================================


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize(
    "text",
    [
        r"Delete every \*.dll in the goblin cache.",
        r"Use \| to separate the potion columns.",
        r"See \_x\_.md for the spellbook index.",
        r"Mount \\server\share before the raid.",
        r"Rename \_dragon\_hoard.json when you are done.",
    ],
    ids=["star-dll", "pipe", "underscore-md", "unc-path", "escaped-json"],
)
def test_escape_sequences_are_not_extended_autolinks(text):
    assert extended_autolinks(text) == []


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize(
    "text",
    [
        "Run ./configure before you summon make.",
        "The ritual is described in ../guide.md and nowhere else.",
    ],
    ids=["dot-slash", "dot-dot-slash"],
)
def test_relative_paths_in_prose_are_not_extended_autolinks(text):
    assert extended_autolinks(text) == []


# ===================================================================
#  Position
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_autolink_position_covers_the_brackets():
    from tiredize.markdown.types.link import Autolink
    text = "Ping <irc://foo.bar:2233/baz> for help"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=5, length=len("<irc://foo.bar:2233/baz>")
    )


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_position_excludes_trailing_punctuation():
    from tiredize.markdown.types.link import ExtendedAutolink
    text = "(see www.commonmark.org/a.b)."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=5, length=len("www.commonmark.org/a.b")
    )


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_base_offset_is_applied():
    from tiredize.markdown.types.link import ExtendedAutolink
    results = ExtendedAutolink.extract("foo@bar.baz", base_offset=300)
    assert len(results) == 1
    assert results[0].position.offset == 300


# ===================================================================
#  Sanitize -- blanks exactly the spans extract() matches
# ===================================================================


@pytest.mark.skip(reason=PENDING)
def test_autolink_sanitize_blanks_exactly_the_bracketed_span():
    from tiredize.markdown.types.link import Autolink
    text = "See <https://example.com> and <foo@bar.example.com> now"
    expected = (
        "See " + " " * len("<https://example.com>")
        + " and " + " " * len("<foo@bar.example.com>")
        + " now"
    )
    assert Autolink.sanitize(text) == expected


@pytest.mark.skip(reason=PENDING)
def test_autolink_sanitize_leaves_non_autolinks_alone():
    from tiredize.markdown.types.link import Autolink
    text = "< http://foo.bar > and <foo.bar.baz> and <m:abc>"
    assert Autolink.sanitize(text) == text


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_sanitize_stops_before_trailing_punctuation():
    from tiredize.markdown.types.link import ExtendedAutolink
    text = "Visit www.commonmark.org."
    expected = "Visit " + " " * len("www.commonmark.org") + "."
    assert ExtendedAutolink.sanitize(text) == expected


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_sanitize_keeps_unmatched_closing_paren():
    from tiredize.markdown.types.link import ExtendedAutolink
    text = "(www.google.com/search?q=Markup+(business))"
    expected = (
        "(" + " " * len("www.google.com/search?q=Markup+(business)") + ")"
    )
    assert ExtendedAutolink.sanitize(text) == expected


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_sanitize_matches_extract_spans():
    """Every character extract() reports is blanked; every other
    character survives. Derived from position, not from a regex."""
    from tiredize.markdown.types.link import ExtendedAutolink
    text = (
        "Mail foo@bar.baz, visit www.commonmark.org/a.b. "
        "and skip ./configure or \\*.dll entirely."
    )
    expected = list(text)
    for link in ExtendedAutolink.extract(text):
        start = link.position.offset
        end = start + link.position.length
        expected[start:end] = " " * (end - start)
    assert ExtendedAutolink.sanitize(text) == "".join(expected)
    assert ExtendedAutolink.sanitize(text) != text


@pytest.mark.skip(reason=PENDING)
def test_extended_autolink_sanitize_leaves_plain_text_alone():
    from tiredize.markdown.types.link import ExtendedAutolink
    text = r"Run ./configure, then \_x\_.md, then a.b-c_d@a.b-"
    assert ExtendedAutolink.sanitize(text) == text
