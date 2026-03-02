# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.quoteblock import QuoteBlock

md_section = """# Markdown Test Section - Lorem Ipsum

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


def test_no_quoteblocks():
    md_test = md_section
    matches = QuoteBlock.extract(md_test)
    assert len(matches) == 0


def test_single_quoteblock_normal():
    depth_01 = 1
    text_01 = "Four score and seven years ago...."
    quote_01 = f"{'>' * depth_01} {text_01}"
    len_01 = len(quote_01)
    position_01 = Position(offset=825, length=len_01)
    md_text = md_section.format(quote_01, "", "", "", "")

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == QuoteBlock(
        depth=depth_01,
        position=position_01,
        quote=text_01,
        string=quote_01
    )


def test_single_quoteblock_multiline():
    depth_01 = 1
    quote_lines = [
        "Four score and seven years ago....",
        "Our fathers brought forth on this continent, a new nation,",
        "conceived in Liberty, and dedicated to the proposition that",
        "all men are created equal."
    ]
    quote_multiline = "> " + "\n> ".join(quote_lines).lstrip("\n")
    len_multiline = len(quote_multiline)
    position_multiline = Position(offset=825, length=len_multiline)
    md_text = md_section.format(quote_multiline, "", "", "", "")

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == QuoteBlock(
        depth=depth_01,
        position=position_multiline,
        quote="\n".join(quote_lines),
        string=quote_multiline
    )


def test_five_quoteblocks_repeated():
    depth_01 = 1
    text_01 = "Four score and seven years ago...."
    quote_01 = f"{'>' * depth_01} {text_01}"
    len_01 = len(quote_01)
    positions = [
        Position(offset=825, length=len_01),
        Position(offset=1271, length=len_01),
        Position(offset=1841, length=len_01),
        Position(offset=2382, length=len_01),
        Position(offset=2915, length=len_01)
    ]

    md_text = md_section.format(
        quote_01,
        quote_01,
        quote_01,
        quote_01,
        quote_01
    )

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == QuoteBlock(
            depth=depth_01,
            string=quote_01,
            position=positions[i],
            quote=text_01
        )


# ===================================================================
#  Edge cases
# ===================================================================


def test_quoteblock_depth_two():
    text = ">> Deeply quoted text"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert matches[0].depth == 2
    assert matches[0].quote == "Deeply quoted text"


def test_quoteblock_base_offset():
    text = "> Some quote"
    matches = QuoteBlock.extract(text, base_offset=50)
    assert len(matches) == 1
    assert matches[0].position.offset == 50


# ===================================================================
#  Sanitize method
# ===================================================================


def test_quoteblock_sanitize_preserves_length():
    text = "Before\n> Quote text\nAfter"
    sanitized = QuoteBlock.sanitize(text)
    assert len(sanitized) == len(text)
    assert "Quote text" not in sanitized


def test_quoteblock_sanitize_no_quotes():
    text = "Just plain text."
    sanitized = QuoteBlock.sanitize(text)
    assert sanitized == text


def test_quoteblock_sanitize_idempotent():
    text = "Before\n> Quote text\nAfter"
    first = QuoteBlock.sanitize(text)
    second = QuoteBlock.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  Syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: lazy continuation in block quotes not supported"
)
def test_quoteblock_lazy_continuation():
    """GFM lazy continuation: line without > continues the quote."""
    text = "> First line\nSecond line (lazy continuation)"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert "Second line" in matches[0].quote


@pytest.mark.skip(reason="gfm-parity: spaced nested quotes parsed as depth 1")
def test_quoteblock_spaced_nested():
    """GFM nested quotes '> > text' should be parsed as depth 2."""
    text = "> > nested quote"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert matches[0].depth == 2
    assert matches[0].quote == "nested quote"


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_quoteblock_extract_empty_string():
    assert QuoteBlock.extract("") == []


def test_quoteblock_extract_single_char():
    """A lone > is a valid empty blockquote per GFM."""
    results = QuoteBlock.extract(">")
    assert len(results) == 1
    assert results[0].depth == 1
    assert results[0].quote == ""


# ===================================================================
#  State mutation
# ===================================================================


def test_quoteblock_extract_does_not_mutate_input():
    text = "> Quote text\n> More quote"
    original = text
    QuoteBlock.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_quoteblock_unicode_content():
    text = "> Café résumé 日本語"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert "Café" in matches[0].quote
    assert "日本語" in matches[0].quote


# ===================================================================
#  Additional syntax variant tests
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: indented block quotes not supported"
)
def test_quoteblock_indented():
    """GFM allows 1-3 spaces before > in block quotes."""
    text = "   > Indented quote"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert matches[0].quote == "Indented quote"


def test_quoteblock_after_pipe_char():
    """The (?<![^|\\n]) anchor treats | as valid start-of-line.
    > after | produces a false positive match."""
    text = "|> Not a real quote"
    matches = QuoteBlock.extract(text)
    # Per GFM, |> is not a blockquote.
    # The anchor accepts | as a valid predecessor.
    assert len(matches) == 1  # documents actual behavior


def test_quoteblock_depth_three():
    """Triple-depth block quote."""
    text = ">>> Deep quote"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    assert matches[0].depth == 3
    assert matches[0].quote == "Deep quote"


def test_quoteblock_empty_lines_between():
    """Adjacent quote blocks separated by blank line should be
    separate matches, not merged."""
    text = "> First\n\n> Second"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 2
    assert matches[0].quote == "First"
    assert matches[1].quote == "Second"


# ===================================================================
#  Cross-cutting: CRLF line endings
# ===================================================================


def test_quoteblock_crlf_in_content():
    """QuoteBlock regex [^\\n]* stops at \\n, so \\r would be
    captured as part of the quote content."""
    text = "> Quote\r\nMore text"
    matches = QuoteBlock.extract(text)
    assert len(matches) == 1
    # \\r is captured because [^\\n]* does not exclude \\r
    assert matches[0].quote == "Quote\r"  # documents actual behavior
