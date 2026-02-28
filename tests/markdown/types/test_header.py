# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.header import Header

md_section = """{}

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean dapibus auctor
mattis. Donec eu posuere ex. Morbi faucibus, diam vitae interdum viverra, diam
nulla tempor tellus, non maximus nulla elit eget arcu. Nam quam turpis, finibus
non velit vel, pellentesque mattis magna. Nunc tempus ultricies pharetra.
Mauris rutrum vel purus eu facilisis. Proin laoreet facilisis libero ac
ultricies. Quisque lectus tellus, maximus nec tellus ut, vestibulum faucibus
nulla. Pellentesque vel ante egestas, aliquet neque a, egestas mauris. Quisque
vulputate metus imperdiet, rhoncus odio eu, dapibus justo. Fusce porta magna in
efficitur tincidunt. Vestibulum efficitur ex porttitor neque suscipit pulvinar.
Nulla mauris libero, semper in ultricies eu, interdum eget justo.

Line 15, Offset 00
{}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu
malesuada eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et
enim pretium rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat.
Mauris vehicula condimentum consequat. Phasellus fermentum rhoncus enim nec
volutpat.

Line 25, Offset 00
{}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et
egestas leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec
maximus ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor.
Vivamus dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at
volutpat nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum.
Nulla vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci,
a fringilla ex. In hac habitasse platea dictumst.

Line 36, Offset 00
{}

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id
arcu porta tempus.

Line 47, Offset 00
{}

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien
eu tortor.

Line 58, Offset 00
{}"""


def test_no_headers():
    md_test = md_section
    matches = Header.extract(md_test)
    assert len(matches) == 0


def test_single_header_level01():
    actual_level = 1
    actual_text = "Header Test: Level One"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-one"
    exp_string = "# Header Test: Level One"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level02():
    actual_level = 2
    actual_text = "Header Test: Level Two"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-two"
    exp_string = "## Header Test: Level Two"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level03():
    actual_level = 3
    actual_text = "Header Test: Level Three"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-three"
    exp_string = "### Header Test: Level Three"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level04():
    actual_level = 4
    actual_text = "Header Test: Level Four"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-four"
    exp_string = "#### Header Test: Level Four"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level05():
    actual_level = 5
    actual_text = "Header Test: Level Five"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-five"
    exp_string = "##### Header Test: Level Five"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level06():
    actual_level = 6
    actual_text = "Header Test: Level Six"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-six"
    exp_string = "###### Header Test: Level Six"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_six_headers_repeated():
    actual_level = 1
    actual_text = "Header Test: Duplicate Level One"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_string = "# Header Test: Duplicate Level One"
    exp_slugs = [
        "#header-test-duplicate-level-one",
        "#header-test-duplicate-level-one-1",
        "#header-test-duplicate-level-one-2",
        "#header-test-duplicate-level-one-3",
        "#header-test-duplicate-level-one-4",
        "#header-test-duplicate-level-one-5",
    ]
    exp_positions = [
        Position(offset=0, length=len(actual_string)),
        Position(offset=822, length=len(actual_string)),
        Position(offset=1266, length=len(actual_string)),
        Position(offset=1834, length=len(actual_string)),
        Position(offset=2373, length=len(actual_string)),
        Position(offset=2904, length=len(actual_string))
    ]

    md_text = md_section.format(
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string
    )
    matches = Header.extract(md_text)
    assert len(matches) == 6
    for i, match in enumerate(matches):
        assert match == Header(
            level=actual_level,
            position=exp_positions[i],
            slug=exp_slugs[i],
            string=exp_string,
            title=actual_text
        )


# ===================================================================
#  Sanitize method (line 70)
# ===================================================================


def test_header_sanitize_preserves_length():
    text = "# Big Title\n\nParagraph below."
    sanitized = Header.sanitize(text)
    assert len(sanitized) == len(text)
    assert "Big Title" not in sanitized


def test_header_sanitize_no_headers():
    text = "Just a paragraph, no headers."
    sanitized = Header.sanitize(text)
    assert sanitized == text


def test_header_sanitize_idempotent():
    text = "# Title\n\n## Subtitle\n"
    first = Header.sanitize(text)
    second = Header.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  slugify_header -- empty title (line 96)
# ===================================================================


def test_slugify_empty_title():
    """Empty string title falls back to 'section'."""
    slug = Header.slugify_header("")
    assert slug == "#section"


def test_slugify_special_characters():
    """Punctuation removed except hyphens."""
    slug = Header.slugify_header("Hello, World! (2024)")
    assert slug == "#hello-world-2024"


def test_slugify_multiple_hyphens_collapsed():
    slug = Header.slugify_header("a - - - b")
    assert slug == "#a-b"


def test_slugify_duplicate_tracking():
    slug = Header.slugify_header("Title", existing=["Title"])
    assert slug == "#title-1"


def test_slugify_multiple_duplicates():
    slug = Header.slugify_header("Title", existing=["Title", "Title"])
    assert slug == "#title-2"


# ===================================================================
#  Edge cases
# ===================================================================


def test_header_seven_hashes_not_matched():
    """GFM only supports 1-6 hashes. Regex \\#{1,6} correctly rejects this."""
    text = "####### Too Many Hashes"
    matches = Header.extract(text)
    assert len(matches) == 0


def test_header_no_space_after_hash_not_matched():
    """GFM requires space after hashes. Correctly rejected."""
    text = "#NoSpace"
    matches = Header.extract(text)
    assert len(matches) == 0


@pytest.mark.skip(reason="gfm-parity: closing hashes not stripped from title")
def test_header_closing_hashes_stripped():
    """GFM strips trailing # characters from heading titles."""
    text = "# Title ##"
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].title == "Title"


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_header_extract_empty_string():
    assert Header.extract("") == []


def test_header_extract_single_char():
    assert Header.extract("#") == []


# ===================================================================
#  State mutation
# ===================================================================


def test_header_extract_does_not_mutate_input():
    text = "# Hello World\n\nParagraph."
    original = text
    Header.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_header_unicode_title():
    text = "# Café Résumé"
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].title == "Café Résumé"


def test_header_emoji_title():
    text = "# Welcome to the Party 🎉"
    matches = Header.extract(text)
    assert len(matches) == 1
    assert "🎉" in matches[0].title


def test_header_unicode_slug():
    """Non-ASCII stripped by [^a-z0-9 \\-] in slugify."""
    slug = Header.slugify_header("Café Résumé")
    assert slug == "#caf-rsum"


# ===================================================================
#  Additional syntax variant tests
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: empty heading not matched"
)
def test_header_empty_heading():
    """GFM allows empty headings: # followed by only whitespace."""
    text = "# "
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].level == 1


@pytest.mark.skip(
    reason="gfm-parity: leading spaces on headings not supported"
)
def test_header_leading_spaces():
    """GFM allows 1-3 spaces before # in headings."""
    text = "   # Indented Heading"
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].title == "Indented Heading"


@pytest.mark.skip(
    reason="gfm-parity: setext headings not supported"
)
def test_header_setext_equals():
    """GFM supports setext headings with = underline (level 1)."""
    text = "Heading\n======="
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].level == 1
    assert matches[0].title == "Heading"


@pytest.mark.skip(
    reason="gfm-parity: setext headings not supported"
)
def test_header_setext_dashes():
    """GFM supports setext headings with - underline (level 2)."""
    text = "Heading\n-------"
    matches = Header.extract(text)
    assert len(matches) == 1
    assert matches[0].level == 2


def test_header_after_pipe_char():
    """The (?<![^|\\n]) anchor treats | as valid start-of-line.
    Header after | produces a false positive match."""
    text = "|# Heading"
    matches = Header.extract(text)
    # Per GFM, |# is not a heading -- it's a table cell.
    # The anchor accepts | as a valid predecessor, causing a
    # false positive.
    assert len(matches) == 1  # documents actual behavior


# ===================================================================
#  Cross-cutting: CRLF line endings
# ===================================================================


def test_header_crlf_in_title():
    """Header title captures content up to \\n via [^\\n]+.
    With CRLF line endings, \\r is captured as part of the title."""
    text = "# Title\r\nParagraph"
    matches = Header.extract(text)
    assert len(matches) == 1
    # \\r is captured as part of title because [^\\n]+ stops at
    # \\n but not at \\r
    assert matches[0].title == "Title\r"  # documents actual behavior


# ===================================================================
#  Cross-cutting: escaped characters
# ===================================================================


def test_header_escaped_hash():
    """Backslash-escaped # should not start a heading per GFM.
    The regex does not handle backslash escapes."""
    text = "\\# Not a heading"
    matches = Header.extract(text)
    # The regex sees # after \\ at start of line. The lookbehind
    # checks the char before #, which is \\. Since \\ is not
    # | or \\n, the lookbehind (?<![^|\\n]) fails and no match.
    assert len(matches) == 0  # accidentally correct
