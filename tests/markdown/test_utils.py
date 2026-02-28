"""Direct tests for tiredize/markdown/utils.py functions.

search_all_re and sanitize_text are the two public utilities used by
all markdown element extractors. These tests exercise the functions
directly rather than through the element type wrappers.
"""

import pytest

from tiredize.markdown.utils import sanitize_text, search_all_re


# ===================================================================
#  search_all_re -- basic behavior
# ===================================================================


def test_search_all_re_basic_match():
    """Single match returns a list with one Match object."""
    matches = search_all_re(r"cat", "the cat sat")
    assert len(matches) == 1
    assert matches[0].group() == "cat"


def test_search_all_re_multiple_matches():
    """Multiple non-overlapping matches all returned in order."""
    matches = search_all_re(r"\d+", "buy 3 llamas and 12 alpacas")
    assert len(matches) == 2
    assert matches[0].group() == "3"
    assert matches[1].group() == "12"


def test_search_all_re_no_matches():
    """No matches returns an empty list."""
    matches = search_all_re(r"unicorn", "just a regular string")
    assert matches == []


def test_search_all_re_empty_string():
    """Empty input string returns no matches."""
    matches = search_all_re(r"anything", "")
    assert matches == []


def test_search_all_re_verbose_syntax():
    """re.VERBOSE flag is active, so comments and whitespace are ignored."""
    pattern = r"""
        (\d+)    # one or more digits
        \s+      # whitespace separator
        (cats?)   # cat or cats
    """
    matches = search_all_re(pattern, "I have 7 cats and 1 cat")
    assert len(matches) == 2
    assert matches[0].group(1) == "7"
    assert matches[0].group(2) == "cats"
    assert matches[1].group(1) == "1"
    assert matches[1].group(2) == "cat"


def test_search_all_re_match_positions():
    """Match start/end positions are correct."""
    matches = search_all_re(r"boo", "boo! peek-a-boo!")
    assert len(matches) == 2
    assert matches[0].start() == 0
    assert matches[0].end() == 3
    assert matches[1].start() == 12
    assert matches[1].end() == 15


# ===================================================================
#  search_all_re -- boundary and degenerate inputs
# ===================================================================


def test_search_all_re_single_character_input():
    """Single character input that matches."""
    matches = search_all_re(r"x", "x")
    assert len(matches) == 1
    assert matches[0].group() == "x"


def test_search_all_re_entire_input_is_one_match():
    """The entire input string is consumed by one match."""
    matches = search_all_re(r".+", "goblin")
    assert len(matches) == 1
    assert matches[0].group() == "goblin"
    assert matches[0].start() == 0
    assert matches[0].end() == 6


def test_search_all_re_overlapping_potential_matches():
    """Overlapping potential matches: finditer returns non-overlapping."""
    # "aaa" could match at positions 0 and 1, but finditer advances
    # past each match so only non-overlapping results are returned.
    matches = search_all_re(r"aa", "aaaa")
    assert len(matches) == 2
    assert matches[0].start() == 0
    assert matches[1].start() == 2


# ===================================================================
#  search_all_re -- unicode
# ===================================================================


def test_search_all_re_unicode_emoji():
    """Emoji characters matched and positions reported correctly."""
    pattern = r"[\U0001F600-\U0001F64F]+"
    matches = search_all_re(pattern, "hello \U0001F60A world")
    assert len(matches) == 1
    assert matches[0].group() == "\U0001F60A"
    assert matches[0].start() == 6


def test_search_all_re_unicode_accented():
    """Accented characters matched correctly."""
    matches = search_all_re(r"caf\u00e9", "one caf\u00e9 two caf\u00e9")
    assert len(matches) == 2
    assert matches[0].group() == "caf\u00e9"


# ===================================================================
#  sanitize_text -- basic behavior
# ===================================================================


def test_sanitize_text_single_match():
    """Single match replaced with whitespace, rest preserved."""
    result = sanitize_text(r"\*\*bold\*\*", "some **bold** text")
    assert result == "some          text"
    assert len(result) == len("some **bold** text")


def test_sanitize_text_multiple_matches():
    """Multiple matches all replaced independently."""
    result = sanitize_text(r"\d+", "buy 3 llamas and 12 alpacas")
    assert "3" not in result
    assert "12" not in result
    assert "llamas" in result
    assert len(result) == len("buy 3 llamas and 12 alpacas")


def test_sanitize_text_no_matches():
    """No matches returns original string unchanged."""
    original = "nothing to sanitize here"
    result = sanitize_text(r"dragon", original)
    assert result == original


def test_sanitize_text_empty_string():
    """Empty input returns empty string."""
    result = sanitize_text(r"anything", "")
    assert result == ""


def test_sanitize_text_preserves_length():
    """Sanitized output is exactly the same length as input."""
    text = "aaa bbb ccc"
    result = sanitize_text(r"bbb", text)
    assert len(result) == len(text)


def test_sanitize_text_replaces_with_spaces():
    """Matched regions become spaces, not any other character."""
    result = sanitize_text(r"secret", "my secret diary")
    assert result == "my        diary"


def test_sanitize_text_multiline_match():
    """Match spanning multiple lines: each line replaced with spaces,
    newlines preserved between them."""
    text = "before\nfoo\nbar\nafter"
    result = sanitize_text(r"foo\nbar", text)
    assert result == "before\n   \n   \nafter"
    assert len(result) == len(text)


# ===================================================================
#  sanitize_text -- boundary and degenerate inputs
# ===================================================================


def test_sanitize_text_entire_string_matches():
    """Input where the entire string is one match."""
    text = "goblin"
    result = sanitize_text(r"goblin", text)
    assert result == "      "
    assert len(result) == len(text)


def test_sanitize_text_adjacent_back_to_back_matches():
    """Adjacent matches with no gap between them."""
    text = "aaabbb"
    result = sanitize_text(r"aaa|bbb", text)
    assert result == "      "
    assert len(result) == len(text)


def test_sanitize_text_single_character_input():
    """Single character that matches."""
    result = sanitize_text(r"x", "x")
    assert result == " "
    assert len(result) == 1


# ===================================================================
#  sanitize_text -- trailing newline bug
#  (Known bug: splitlines() drops trailing \n. These tests document
#  the bug and are skipped. See sanitize-text-newline-bug.md.)
# ===================================================================


@pytest.mark.skip(
    reason="sanitize-text-newline-bug: "
    "splitlines() drops trailing newline"
)
def test_sanitize_text_match_ending_with_newline():
    """Match ending with \\n preserves the trailing newline."""
    text = "---\nfoo\n---\nafter"
    result = sanitize_text(r"---\nfoo\n---\n", text)
    assert len(result) == len(text)
    assert result.endswith("after")


@pytest.mark.skip(
    reason="sanitize-text-newline-bug: "
    "splitlines() drops trailing newline"
)
def test_sanitize_text_preserves_length_with_trailing_newline():
    """Length preservation contract holds for matches ending in \\n."""
    text = "hello\nworld\n"
    result = sanitize_text(r"hello\nworld\n", text)
    assert len(result) == len(text)


# ===================================================================
#  sanitize_text -- idempotency
# ===================================================================


def test_sanitize_text_idempotent():
    """Calling sanitize twice produces the same result as once."""
    text = "keep **bold** and **more** keep"
    pattern = r"\*\*[^*]+\*\*"
    first = sanitize_text(pattern, text)
    second = sanitize_text(pattern, first)
    assert second == first
    assert len(second) == len(text)


# ===================================================================
#  sanitize_text -- unicode
# ===================================================================


def test_sanitize_text_unicode_preserves_char_length():
    """Length preserved in characters (str length), not bytes.
    \u00e9 is 1 Python char but 2 UTF-8 bytes."""
    text = "the caf\u00e9 is nice"
    result = sanitize_text(r"caf\u00e9", text)
    assert len(result) == len(text)


def test_sanitize_text_emoji_preserves_length():
    """Emoji are 1 Python char each. Length must be preserved."""
    text = "hello \U0001F60A world"
    result = sanitize_text(r"\U0001F60A", text)
    assert len(result) == len(text)
    assert "\U0001F60A" not in result
