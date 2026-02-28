# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.link import BareLink
from tiredize.markdown.types.link import BracketLink
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
#  BracketLink -- basic extraction
# ===================================================================


def test_bracket_link_basic():
    text = "<https://example.com>"
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert results[0].string == text


def test_bracket_link_http():
    text = "<http://insecure.example.com>"
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "http://insecure.example.com"


def test_bracket_link_with_path():
    text = "<https://example.com/path?q=1&r=2>"
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/path?q=1&r=2"


def test_bracket_link_multiple():
    text = "See <https://a.com> and <https://b.com> for details."
    results = BracketLink.extract(text)
    assert len(results) == 2
    assert results[0].url == "https://a.com"
    assert results[1].url == "https://b.com"


def test_bracket_link_no_matches():
    text = "No angle bracket links here."
    results = BracketLink.extract(text)
    assert len(results) == 0


def test_bracket_link_position_tracking():
    text = "Check <https://example.com> now."
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=6, length=len("<https://example.com>")
    )


def test_bracket_link_base_offset():
    text = "<https://example.com>"
    results = BracketLink.extract(text, base_offset=50)
    assert len(results) == 1
    assert results[0].position.offset == 50


# ===================================================================
#  BracketLink -- sanitize
# ===================================================================


def test_bracket_link_sanitize_preserves_length():
    text = "Before <https://example.com> after"
    sanitized = BracketLink.sanitize(text)
    assert len(sanitized) == len(text)
    assert "<https://example.com>" not in sanitized


# ===================================================================
#  BareLink -- basic extraction
# ===================================================================


def test_bare_link_https():
    text = "Visit https://example.com for more."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


def test_bare_link_http():
    text = "Visit http://example.com for more."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "http://example.com"


def test_bare_link_relative_dot_slash():
    text = "See ./docs/readme.md for details."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "./docs/readme.md"


def test_bare_link_backslash():
    text = r"See \docs\readme.md for details."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == r"\docs\readme.md"


def test_bare_link_multiple():
    text = "Visit https://a.com and https://b.com today."
    results = BareLink.extract(text)
    assert len(results) == 2
    assert results[0].url == "https://a.com"
    assert results[1].url == "https://b.com"


def test_bare_link_no_matches():
    text = "No URLs here, just words."
    results = BareLink.extract(text)
    assert len(results) == 0


def test_bare_link_position_tracking():
    text = "Go to https://example.com now."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(
        offset=6, length=len("https://example.com")
    )


def test_bare_link_base_offset():
    text = "https://example.com"
    results = BareLink.extract(text, base_offset=200)
    assert len(results) == 1
    assert results[0].position.offset == 200


# ===================================================================
#  BareLink -- sanitize
# ===================================================================


def test_bare_link_sanitize_preserves_length():
    text = "Visit https://example.com today"
    sanitized = BareLink.sanitize(text)
    assert len(sanitized) == len(text)
    assert "https://example.com" not in sanitized


# ===================================================================
#  BareLink -- sanitization chain
#  BareLink sanitizes: CodeBlock, CodeInline, QuoteBlock, InlineImage,
#  BracketLink, InlineLink, ReferenceDefinition before matching.
# ===================================================================


def test_bare_link_not_inside_inline_link():
    """A URL inside [text](url) should not also appear as a BareLink."""
    text = "[click](https://example.com)"
    results = BareLink.extract(text)
    assert len(results) == 0


def test_bare_link_not_inside_bracket_link():
    """A URL inside <url> should not also appear as a BareLink."""
    text = "<https://example.com>"
    results = BareLink.extract(text)
    assert len(results) == 0


def test_bare_link_not_inside_code_inline():
    """A URL inside backticks should not appear as a BareLink."""
    text = "Run `https://example.com` as a test."
    results = BareLink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links not extracted from code blocks
# ===================================================================


def test_inline_link_not_inside_code_block():
    """InlineLink sanitizes CodeBlock, so links in fences are excluded."""
    text = "```\n[link](https://example.com)\n```"
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_bracket_link_not_inside_code_block():
    text = "```\n<https://example.com>\n```"
    results = BracketLink.extract(text)
    assert len(results) == 0


def test_bare_link_not_inside_code_block():
    text = "```\nhttps://example.com\n```"
    results = BareLink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links not extracted from inline code
# ===================================================================


def test_inline_link_not_inside_inline_code():
    """InlineLink sanitizes CodeInline."""
    text = "Use `[link](https://example.com)` as example."
    results = InlineLink.extract(text)
    assert len(results) == 0


def test_bracket_link_not_inside_inline_code():
    text = "Use `<https://example.com>` as example."
    results = BracketLink.extract(text)
    assert len(results) == 0


def test_bare_link_not_inside_inline_code():
    text = "Use `https://example.com` as example."
    results = BareLink.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: links inside quote blocks
#  InlineLink/BracketLink sanitize QuoteBlock. BareLink also sanitizes it.
#  The `>` is sanitized, so the link text after sanitization may still
#  match. Document actual behavior.
# ===================================================================


@pytest.mark.skip(
    reason="QuoteBlock sanitize removes content that contains valid links"
)
def test_inline_link_inside_quote_block():
    """Per GFM, links inside blockquotes are real links and should be
    extracted. QuoteBlock sanitize is too aggressive."""
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
def test_bracket_link_ftp():
    """GFM autolinks support ftp:// scheme."""
    text = "<ftp://files.example.com>"
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "ftp://files.example.com"


@pytest.mark.skip(reason="gfm-parity: email autolinks not supported")
def test_bracket_link_email():
    """GFM supports email autolinks in angle brackets."""
    text = "<user@example.com>"
    results = BracketLink.extract(text)
    assert len(results) == 1


@pytest.mark.skip(reason="gfm-parity: www. autolinks not supported")
def test_bare_link_www():
    """GFM extended autolinks recognize www. prefix without scheme."""
    text = "Visit www.example.com for details."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "www.example.com"


@pytest.mark.skip(
    reason="gfm-parity: trailing punctuation not stripped from URLs"
)
def test_bare_link_trailing_punctuation_stripped():
    """GFM strips trailing punctuation from extended autolinks."""
    text = "Visit https://example.com."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


@pytest.mark.skip(
    reason="gfm-parity: ../ relative paths produce false partial match"
)
def test_bare_link_parent_dir_not_partial_match():
    """Relative paths with ../ should not produce a false partial match
    of ./sibling/ from position 1 of ../."""
    text = "See ../sibling/readme.md for details."
    results = BareLink.extract(text)
    # Either match the full ../sibling/readme.md or don't match at all
    assert len(results) == 0 or results[0].url == "../sibling/readme.md"


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_inline_link_empty_string():
    assert InlineLink.extract("") == []


def test_bracket_link_empty_string():
    assert BracketLink.extract("") == []


def test_bare_link_empty_string():
    assert BareLink.extract("") == []


def test_inline_link_single_char():
    assert InlineLink.extract("x") == []


def test_bracket_link_single_char():
    assert BracketLink.extract("<") == []


def test_bare_link_single_char():
    assert BareLink.extract("h") == []


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


def test_bracket_link_sanitize_idempotent():
    text = "Before <https://example.com> after"
    first = BracketLink.sanitize(text)
    second = BracketLink.sanitize(first)
    assert first == second
    assert len(second) == len(text)


def test_bare_link_sanitize_idempotent():
    text = "Before https://example.com after"
    first = BareLink.sanitize(text)
    second = BareLink.sanitize(first)
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


def test_bracket_link_extract_does_not_mutate_input():
    text = "See <https://example.com> here."
    original = text
    BracketLink.extract(text)
    assert text == original


def test_bare_link_extract_does_not_mutate_input():
    text = "See https://example.com here."
    original = text
    BareLink.extract(text)
    assert text == original


# ===================================================================
#  Unicode and non-ASCII
# ===================================================================


def test_inline_link_unicode_text_and_url():
    text = "[café guide](https://example.com/café)"
    results = InlineLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/café"


def test_bracket_link_unicode_url():
    text = "<https://example.com/日本語>"
    results = BracketLink.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com/日本語"


def test_bare_link_unicode_url():
    text = "Visit https://example.com/über-cool page."
    results = BareLink.extract(text)
    assert len(results) == 1
    assert "über-cool" in results[0].url
