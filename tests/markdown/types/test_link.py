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


@pytest.mark.skip(reason="gfm-parity: non-HTTP URI schemes not supported")
def test_autolink_ftp():
    """GFM autolinks support ftp:// scheme."""
    text = "<ftp://files.example.com>"
    results = Autolink.extract(text)
    assert len(results) == 1
    assert results[0].url == "ftp://files.example.com"


@pytest.mark.skip(reason="gfm-parity: email autolinks not supported")
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
