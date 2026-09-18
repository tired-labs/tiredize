# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.link import Autolink
from tiredize.markdown.types.link import ExtendedAutolink
from tiredize.markdown.types.link import InlineLink


# ===================================================================
#  InlineLink -- basic extraction
# ===================================================================


def test_inline_link_basic():
    text = "[click here](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].title is None
    assert results[0].string == text


def test_inline_link_with_title():
    text = '[link](https://example.com "Fancy Title")'
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].title == "Fancy Title"


def test_inline_link_whitespace_around_text():
    text = "[ spaced text ](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_inline_link_empty_text():
    text = "[](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_inline_link_multiple():
    text = "Visit [a](https://a.com) or [b](https://b.com) today."
    results = InlineLink.extract(text)
    assert len(results) == 2
    assert results[0].url == "https://a.com"
    assert results[1].url == "https://b.com"


def test_inline_link_no_matches():
    text = "Just some plain text without any links at all."
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_inline_link_position_tracking():
    text = "Hello [link](https://example.com) world"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=6, length=len("[link](https://example.com)")
    )


def test_inline_link_base_offset():
    text = "[link](https://example.com)"
    results = InlineLink.extract(text, base_offset=100)
    assert len(results) == 1
    assert results[0].position.offset == 100


def test_inline_link_not_image():
    """InlineLink must not match image syntax ![alt](url)."""
    text = "![kitten](https://cats.com/meow.png)"
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_inline_link_adjacent_to_image():
    """InlineLink after an image should be captured separately."""
    text = "![img](a.png)[link](b.html)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "b.html"


# ===================================================================
#  InlineLink -- sanitize
# ===================================================================


def test_inline_link_sanitize_preserves_length():
    text = "Before [link](https://example.com) after"
    sanitized = InlineLink.sanitize(text)
    assert len(sanitized) == len(text)
    assert "https://example.com" not in sanitized


def test_inline_link_sanitize_replaces_with_whitespace():
    text = "[click](https://example.com)"
    sanitized = InlineLink.sanitize(text)
    assert sanitized == " " * len(text)


# ===================================================================
#  Autolink -- basic extraction
# ===================================================================


def test_autolink_basic():
    text = "<https://example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].string == text


def test_autolink_http():
    text = "<http://insecure.example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "http://insecure.example.com"


def test_autolink_with_path():
    text = "<https://example.com/path?q=1&r=2>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/path?q=1&r=2"


def test_autolink_multiple():
    text = "See <https://a.com> and <https://b.com> for details."
    results = Autolink.extract(text)
    assert len(results) == 2
    assert results[0].url == "https://a.com"
    assert results[1].url == "https://b.com"


def test_autolink_no_matches():
    text = "No angle bracket links here."
    results = Autolink.extract(text)
    assert len(results) == 0


def test_autolink_position_tracking():
    text = "Check <https://example.com> now."
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=6, length=len("<https://example.com>")
    )


def test_autolink_base_offset():
    text = "<https://example.com>"
    results = Autolink.extract(text, base_offset=50)
    assert len(results) == 1
    assert results[0].position.offset == 50


# ===================================================================
#  Autolink -- sanitize
# ===================================================================


def test_autolink_sanitize_preserves_length():
    text = "Before <https://example.com> after"
    sanitized = Autolink.sanitize(text)
    assert len(sanitized) == len(text)
    assert "<https://example.com>" not in sanitized


# ===================================================================
#  Autolink -- GFM 6.8 boundaries (white-box)
#
#  The specification examples live in test_link_gfm_autolinks.py.
#  These pin the edges of the rules those examples illustrate: the
#  scheme length and character set, the characters a URI may not
#  contain, the HTML5 email label limits, and which branch wins when
#  both could apply.
# ===================================================================


def _autolinks(text: str) -> list[tuple[str, str]]:
    return [(link.string, link.url) for link in Autolink.extract(text)]


def test_autolink_scheme_two_characters_is_the_minimum():
    assert _autolinks("<ab:c>") == [("<ab:c>", "ab:c")]
    assert _autolinks("<a:c>") == []


def test_autolink_scheme_thirty_two_characters_is_the_maximum():
    scheme_32 = "s" + "c" * 31
    scheme_33 = scheme_32 + "c"
    assert _autolinks(f"<{scheme_32}:x>") == [
        (f"<{scheme_32}:x>", f"{scheme_32}:x"),
    ]
    assert _autolinks(f"<{scheme_33}:x>") == []


def test_autolink_scheme_must_start_with_a_letter():
    assert _autolinks("<1ab:c>") == []
    assert _autolinks("<+ab:c>") == []


def test_autolink_scheme_allows_plus_dot_and_hyphen_only():
    assert _autolinks("<a+b.c-d:e>") == [("<a+b.c-d:e>", "a+b.c-d:e")]
    assert _autolinks("<a_b:c>") == []
    assert _autolinks("<a/b:c>") == []


def test_autolink_uri_may_be_empty_after_the_colon():
    assert _autolinks("<ab:>") == [("<ab:>", "ab:")]


@pytest.mark.parametrize(
    "bad",
    ["\t", "\n", "\r", "\x00", "\x1f", "\x7f", "<"],
    ids=["tab", "newline", "cr", "nul", "unit-sep", "del", "lt"],
)
def test_autolink_uri_rejects_ascii_whitespace_control_and_brackets(bad):
    assert _autolinks(f"<https://a.b/x{bad}y>") == []


def test_autolink_uri_keeps_non_ascii_and_punctuation():
    text = "<https://a.b/日本語?q=1&r=[2]#frag'\"`>"
    assert _autolinks(text) == [
        (text, "https://a.b/日本語?q=1&r=[2]#frag'\"`"),
    ]


def test_autolink_uri_branch_wins_over_email_branch():
    """`mailto:x@y.z` is a URI with scheme `mailto`, so the target is
    the text as written -- no second `mailto:` is prepended."""
    assert _autolinks("<mailto:x@y.z>") == [("<mailto:x@y.z>", "mailto:x@y.z")]


def test_autolink_email_domain_without_a_dot_is_allowed():
    """The HTML5 regex makes the dotted labels optional."""
    assert _autolinks("<x@y>") == [("<x@y>", "mailto:x@y")]


def test_autolink_email_local_part_allows_html5_specials():
    local = "a.!#$%&'*+/=?^_`{|}~-"
    text = f"<{local}@b.c>"
    assert _autolinks(text) == [(text, f"mailto:{local}@b.c")]


def test_autolink_email_local_part_rejects_other_characters():
    assert _autolinks("<a b@c.d>") == []
    assert _autolinks('<a"b@c.d>') == []
    assert _autolinks("<a\\b@c.d>") == []


def test_autolink_email_label_may_not_start_or_end_with_a_hyphen():
    assert _autolinks("<a@-b.c>") == []
    assert _autolinks("<a@b-.c>") == []
    assert _autolinks("<a@b.-c>") == []
    assert _autolinks("<a@b-c.d>") == [("<a@b-c.d>", "mailto:a@b-c.d")]


def test_autolink_email_label_sixty_three_characters_is_the_maximum():
    label_63 = "x" * 63
    label_64 = "x" * 64
    assert _autolinks(f"<a@{label_63}.c>") == [
        (f"<a@{label_63}.c>", f"mailto:a@{label_63}.c"),
    ]
    assert _autolinks(f"<a@{label_64}.c>") == []


def test_autolink_email_rejects_empty_label():
    assert _autolinks("<a@b..c>") == []
    assert _autolinks("<a@.b>") == []


def test_autolink_stops_at_the_first_closing_bracket():
    text = "<https://a.b/x>y>"
    assert _autolinks(text) == [("<https://a.b/x>", "https://a.b/x")]


def test_autolink_position_after_non_ascii_prefix():
    text = "日本 <https://a.b>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=3, length=len("<https://a.b>")
    )


def test_autolink_sanitize_blanks_uri_and_email_forms_across_lines():
    text = "one <irc://a.b>\ntwo <x@y.z>"
    expected = (
        "one " + " " * len("<irc://a.b>")
        + "\ntwo " + " " * len("<x@y.z>")
    )
    assert Autolink.sanitize(text) == expected


# ===================================================================
#  ExtendedAutolink -- basic extraction
# ===================================================================


def test_extended_autolink_https():
    text = "Visit https://example.com for more."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_extended_autolink_http():
    text = "Visit http://example.com for more."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "http://example.com"


def test_extended_autolink_relative_dot_slash():
    text = "See ./docs/readme.md for details."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "./docs/readme.md"


def test_extended_autolink_backslash():
    text = r"See \docs\readme.md for details."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == r"\docs\readme.md"


def test_extended_autolink_backslash_not_matched_mid_word():
    text = r'Registry key: "HKLM\SYSTEM\CurrentControlSet\Control"'
    results = ExtendedAutolink.extract(text)
    assert results == []


def test_extended_autolink_multiple():
    text = "Visit https://a.com and https://b.com today."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 2
    assert results[0].url == "https://a.com"
    assert results[1].url == "https://b.com"


def test_extended_autolink_no_matches():
    text = "No URLs here, just words."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


def test_extended_autolink_position_tracking():
    text = "Go to https://example.com now."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=6, length=len("https://example.com")
    )


def test_extended_autolink_base_offset():
    text = "https://example.com"
    results = ExtendedAutolink.extract(text, base_offset=200)
    assert len(results) == 1
    assert results[0].position.offset == 200


# ===================================================================
#  ExtendedAutolink -- sanitize
# ===================================================================


def test_extended_autolink_sanitize_preserves_length():
    text = "Visit https://example.com today"
    sanitized = ExtendedAutolink.sanitize(text)
    assert len(sanitized) == len(text)
    assert "https://example.com" not in sanitized


# ===================================================================
#  ExtendedAutolink -- sanitization chain
#  ExtendedAutolink sanitizes: CodeBlock, CodeInline, InlineImage,
#  Autolink, InlineLink, ReferenceDefinition before matching.
# ===================================================================


def test_extended_autolink_not_inside_inline_link():
    """A URL inside [text](url) should not also appear as an
    ExtendedAutolink."""
    text = "[click](https://example.com)"
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


def test_extended_autolink_not_inside_autolink():
    """A URL inside <url> should not also appear as an ExtendedAutolink."""
    text = "<https://example.com>"
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


def test_extended_autolink_not_inside_code_inline():
    """A URL inside backticks should not appear as an ExtendedAutolink."""
    text = "Run `https://example.com` as a test."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links not extracted from code blocks
# ===================================================================


def test_inline_link_not_inside_code_block():
    """InlineLink sanitizes CodeBlock, so links in fences are excluded."""
    text = "```\n[link](https://example.com)\n```"
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_autolink_not_inside_code_block():
    text = "```\n<https://example.com>\n```"
    results = Autolink.extract(text)
    assert len(results) == 0


def test_extended_autolink_not_inside_code_block():
    text = "```\nhttps://example.com\n```"
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links not extracted from inline code
# ===================================================================


def test_inline_link_not_inside_inline_code():
    """InlineLink sanitizes CodeInline."""
    text = "Use `[link](https://example.com)` as example."
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_autolink_not_inside_inline_code():
    text = "Use `<https://example.com>` as example."
    results = Autolink.extract(text)
    assert len(results) == 0


def test_extended_autolink_not_inside_inline_code():
    text = "Use `https://example.com` as example."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links inside quote blocks
#  Link extractors do not sanitize QuoteBlock. The > prefix does not
#  interfere with link regex patterns, so links inside blockquotes
#  are correctly extracted.
# ===================================================================


def test_inline_link_inside_quote_block():
    """Per GFM, links inside blockquotes are real links and should be
    extracted."""
    text = "> [link](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


# ===================================================================
#  Syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(reason="gfm-parity: single-quote titles not supported")
def test_inline_link_single_quote_title():
    """GFM allows single-quote titles in inline links."""
    text = "[link](https://example.com 'A Title')"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].title == "A Title"


@pytest.mark.skip(reason="gfm-parity: empty URL in inline links not supported")
def test_inline_link_empty_url():
    """GFM allows empty URLs [text]()."""
    text = "[link]()"
    results = InlineLink.extract(text)
    assert len(results) == 1


@pytest.mark.skip(
    reason="gfm-parity: escaped brackets in link text not supported"
)
def test_inline_link_escaped_bracket_in_text():
    r"""GFM allows \] inside link text via backslash escape."""
    text = r"[text \] here](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_autolink_ftp():
    """GFM autolinks support ftp:// scheme."""
    text = "<ftp://files.example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "ftp://files.example.com"


def test_autolink_email():
    """GFM supports email autolinks in angle brackets."""
    text = "<user@example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1


@pytest.mark.skip(reason="gfm-parity: www. autolinks not supported")
def test_extended_autolink_www():
    """GFM extended autolinks recognize www. prefix without scheme."""
    text = "Visit www.example.com for details."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "www.example.com"


@pytest.mark.skip(
    reason="gfm-parity: trailing punctuation not stripped from URLs"
)
def test_extended_autolink_trailing_punctuation_stripped():
    """GFM strips trailing punctuation from extended autolinks."""
    text = "Visit https://example.com."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_extended_autolink_parent_dir_not_partial_match():
    """Relative paths with ../ should match the full path, not a
    false partial match of ./sibling/ from position 1."""
    text = "See ../sibling/readme.md for details."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "../sibling/readme.md"


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_inline_link_empty_string():
    assert InlineLink.extract("") == []


def test_autolink_empty_string():
    assert Autolink.extract("") == []


def test_extended_autolink_empty_string():
    assert ExtendedAutolink.extract("") == []


def test_inline_link_single_char():
    assert InlineLink.extract("x") == []


def test_autolink_single_char():
    assert Autolink.extract("<") == []


def test_extended_autolink_single_char():
    assert ExtendedAutolink.extract("h") == []


def test_inline_link_no_trailing_newline():
    text = "[link](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1


# ===================================================================
#  Idempotency
# ===================================================================


def test_inline_link_sanitize_idempotent():
    text = "Before [link](https://example.com) after"
    first = InlineLink.sanitize(text)
    second = InlineLink.sanitize(first)
    assert first == second
    assert len(second) == len(text)


def test_autolink_sanitize_idempotent():
    text = "Before <https://example.com> after"
    first = Autolink.sanitize(text)
    second = Autolink.sanitize(first)
    assert first == second
    assert len(second) == len(text)


def test_extended_autolink_sanitize_idempotent():
    text = "Before https://example.com after"
    first = ExtendedAutolink.sanitize(text)
    second = ExtendedAutolink.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  State mutation
# ===================================================================


def test_inline_link_extract_does_not_mutate_input():
    text = "See [link](https://example.com) here."
    original = text
    InlineLink.extract(text)
    assert text == original


def test_autolink_extract_does_not_mutate_input():
    text = "See <https://example.com> here."
    original = text
    Autolink.extract(text)
    assert text == original


def test_extended_autolink_extract_does_not_mutate_input():
    text = "See https://example.com here."
    original = text
    ExtendedAutolink.extract(text)
    assert text == original


# ===================================================================
#  Unicode and non-ASCII
# ===================================================================


def test_inline_link_unicode_text_and_url():
    text = "[café guide](https://example.com/café)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/café"


def test_autolink_unicode_url():
    text = "<https://example.com/日本語>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/日本語"


def test_extended_autolink_unicode_url():
    text = "Visit https://example.com/über-cool page."
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert "über-cool" in results[0].url


# ===================================================================
#  Cross-type: links inside tables
# ===================================================================


def test_inline_link_inside_table_cell():
    """Links in table cells are real links per GFM and should be
    extracted. InlineLink does not sanitize Table."""
    text = "| [link](https://example.com) |\n|---|\n| data |\n"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_autolink_inside_table_cell():
    """Autolinks in table cells should be extracted."""
    text = "| <https://example.com> |\n|---|\n| data |\n"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_extended_autolink_inside_table_cell():
    """Extended autolinks in table cells should be extracted."""
    text = "| https://example.com |\n|---|\n| data |\n"
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


# ===================================================================
#  Cross-type: links inside quote blocks
# ===================================================================


def test_autolink_inside_quote_block():
    """Per GFM, links inside blockquotes are real links."""
    text = "> <https://example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_extended_autolink_inside_quote_block():
    """Per GFM, links inside blockquotes are real links."""
    text = "> https://example.com"
    results = ExtendedAutolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


# ===================================================================
#  InlineLink -- additional syntax variants
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: parenthesis title delimiters not supported"
)
def test_inline_link_parens_title():
    """GFM allows (title) as title delimiter."""
    text = "[link](https://example.com (A Title))"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].title == "A Title"


@pytest.mark.skip(
    reason="gfm-parity: angle-bracket URLs not supported"
)
def test_inline_link_angle_bracket_url():
    """GFM allows <url with spaces> in inline links."""
    text = "[link](<https://example.com/path with spaces>)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/path with spaces"


@pytest.mark.skip(
    reason="gfm-parity: nested brackets in link text not handled"
)
def test_inline_link_nested_brackets():
    """GFM handles nested brackets in link text."""
    text = "[text [nested]](https://example.com)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


@pytest.mark.skip(
    reason="gfm-parity: escaped quote in title truncates match"
)
def test_inline_link_escaped_quote_in_title():
    r"""GFM handles \" inside double-quoted titles."""
    text = r'[link](https://example.com "title \" here")'
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].title == r'title " here'
