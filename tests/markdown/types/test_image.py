# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.image import InlineImage


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

Line 14, Offset 19 {}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu
malesuada eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et
enim pretium rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat.
Mauris vehicula condimentum consequat. Phasellus fermentum rhoncus enim nec
volutpat.

Line 23
Offset 10 {}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et
egestas leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec
maximus ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor.
Vivamus dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at
volutpat nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum.
Nulla vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci,
a fringilla ex. In hac habitasse platea dictumst.

Line 34 with an offset of 29 {} and surrounding text.

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id
arcu porta tempus.

L44, O09 {} with surrounding text.

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien
eu tortor.

L54, Offset 15 {}"""


def test_no_images():
    md_test = md_section
    matches = InlineImage.extract(md_test)
    assert len(matches) == 0


def test_single_image_normal():
    actual_alttext = "Alt Text"
    actual_url = "https://tired.labs/eye.svg"
    actual_title = "Image Title"
    actual_string = f"![{actual_alttext}]({actual_url} \"{actual_title}\")"
    position = Position(offset=825, length=len(actual_string))
    md_text = md_section.format(actual_string, "", "", "", "")

    exp_string = '![Alt Text](https://tired.labs/eye.svg "Image Title")'

    matches = InlineImage.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == InlineImage(
        position=position,
        string=exp_string,
        text=actual_alttext,
        title=actual_title,
        url=actual_url
    )


def test_five_images_repeated():
    actual_alttext = "Alt Text"
    actual_url = "https://tired.labs/eye.svg"
    actual_title = "Image Title"
    actual_string = f"![{actual_alttext}]({actual_url} \"{actual_title}\")"

    exp_string = '![Alt Text](https://tired.labs/eye.svg "Image Title")'
    exp_positions = [
        Position(offset=825, length=len(actual_string)),
        Position(offset=1287, length=len(actual_string)),
        Position(offset=1884, length=len(actual_string)),
        Position(offset=2454, length=len(actual_string)),
        Position(offset=3023, length=len(actual_string))
    ]

    md_text = md_section.format(
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string
    )
    matches = InlineImage.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == InlineImage(
            position=exp_positions[i],
            string=exp_string,
            text=actual_alttext,
            title=actual_title,
            url=actual_url
        )


def test_five_images_unique():
    actual: list[str] = []
    expected: list[InlineImage] = []

    alt_text_values = [
        "Image 01 Alt Text",
        "Second Alt Text",
        "No Title for the 3rd Image",
        "Local Image for the Fourth Test",
        "Fifth Image With Alt Text",
    ]
    position_values = [825, 1302, 1906, 2476, 3048]
    title_values = [
        "Image 01 Title",
        "Title 2",
        "",
        "",
        "4th"
    ]
    url_values = [
        "https://first.com/image01.png",
        "https://secondvisual.com/2.jpg",
        "https://3.com/3.png",
        "./images/img4.svg",
        "https://tired.labs/eye.svg"
    ]
    expected_strings = [
        '![Image 01 Alt Text](https://first.com/image01.png "Image 01 Title")',
        '![Second Alt Text](https://secondvisual.com/2.jpg "Title 2")',
        '![No Title for the 3rd Image](https://3.com/3.png "")',
        '![Local Image for the Fourth Test](./images/img4.svg "")',
        '![Fifth Image With Alt Text](https://tired.labs/eye.svg "4th")'
    ]

    for i in range(5):
        actual_alttext = f"{alt_text_values[i]}"
        actual_url = f"{url_values[i]}"
        actual_title = ""
        if len(title_values[i]) > 0:
            actual_title = f"{title_values[i]}"
        actual_string = f"![{actual_alttext}]({actual_url} \"{actual_title}\")"
        actual.append(actual_string)

        expected.append(
            InlineImage(
                position=Position(
                    offset=position_values[i],
                    length=len(actual_string)
                ),
                string=expected_strings[i],
                text=alt_text_values[i],
                title=title_values[i],
                url=url_values[i]
            )
        )

    md_text = md_section.format(
        actual[0],
        actual[1],
        actual[2],
        actual[3],
        actual[4]
    )

    matches = InlineImage.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == expected[i]


# ===================================================================
#  Sanitize method
# ===================================================================


def test_image_sanitize_preserves_length():
    text = 'See ![alt](https://img.com/pic.png "title") here.'
    sanitized = InlineImage.sanitize(text)
    assert len(sanitized) == len(text)
    assert "img.com" not in sanitized


def test_image_sanitize_no_images():
    text = "No images here."
    sanitized = InlineImage.sanitize(text)
    assert sanitized == text


def test_image_sanitize_idempotent():
    text = "![alt](https://img.com/pic.png)"
    first = InlineImage.sanitize(text)
    second = InlineImage.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  Cross-type: image not extracted as InlineLink
# ===================================================================


def test_image_not_extracted_as_inline_link():
    """InlineLink has negative lookbehind (?<!!) to avoid images."""
    from tiredize.markdown.types.link import InlineLink
    text = "![alt](https://img.com/pic.png)"
    results = InlineLink.extract(text)
    assert len(results) == 0


@pytest.mark.skip(
    reason="gfm-parity: greedy URL regex consumes past closing paren"
)
def test_image_adjacent_to_link():
    """![img](a.png)[link](b.html) -- image URL should be 'a.png',
    not greedily extended through the adjacent link syntax."""
    text = "![img](a.png)[link](b.html)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].url == "a.png"


# ===================================================================
#  Cross-type: image inside code block (no sanitization)
# ===================================================================


@pytest.mark.skip(reason="InlineImage does not sanitize CodeBlock")
def test_image_not_inside_code_block():
    """Images inside fenced code blocks should not be extracted."""
    text = "```\n![alt](https://img.com/pic.png)\n```"
    results = InlineImage.extract(text)
    assert len(results) == 0


@pytest.mark.skip(reason="InlineImage does not sanitize CodeInline")
def test_image_not_inside_inline_code():
    """Images inside inline code should not be extracted."""
    text = "Use `![alt](https://img.com/pic.png)` as example."
    results = InlineImage.extract(text)
    assert len(results) == 0


# ===================================================================
#  Edge cases
# ===================================================================


def test_image_no_title():
    text = "![alt](https://img.com/pic.png)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].title is None


def test_image_base_offset():
    text = "![alt](https://img.com/pic.png)"
    results = InlineImage.extract(text, base_offset=42)
    assert len(results) == 1
    assert results[0].position.offset == 42


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_image_extract_empty_string():
    assert InlineImage.extract("") == []


def test_image_extract_single_char():
    assert InlineImage.extract("!") == []


# ===================================================================
#  Syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(reason="gfm-parity: empty URL in images not supported")
def test_image_empty_url():
    """GFM allows empty URLs ![alt]()."""
    text = "![alt]()"
    results = InlineImage.extract(text)
    assert len(results) == 1


# ===================================================================
#  State mutation
# ===================================================================


def test_image_extract_does_not_mutate_input():
    text = "![alt](https://img.com/pic.png)"
    original = text
    InlineImage.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_image_unicode_alt_text():
    text = "![日本語の画像](https://img.com/pic.png)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].text == "日本語の画像"


def test_image_unicode_url():
    text = "![alt](https://img.com/café.png)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert "café" in results[0].url


# ===================================================================
#  Cross-type: images inside quote blocks
# ===================================================================


def test_image_inside_quote_block():
    """InlineImage does not sanitize QuoteBlock.
    Per GFM, images inside blockquotes are real images.
    InlineImage does NO sanitization at all, so this should match
    -- but the ! may be preceded by > whitespace which doesn't
    interfere with the regex."""
    text = "> ![alt](https://img.com/pic.png)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://img.com/pic.png"


# ===================================================================
#  InlineImage -- additional syntax variants
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: single-quote titles not supported"
)
def test_image_single_quote_title():
    """GFM allows single-quote titles in images."""
    text = "![alt](https://img.com/pic.png 'A Title')"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].title == "A Title"


@pytest.mark.skip(
    reason="gfm-parity: angle-bracket URLs not supported"
)
def test_image_angle_bracket_url():
    """GFM allows <url with spaces> in images."""
    text = "![alt](<https://img.com/path with spaces.png>)"
    results = InlineImage.extract(text)
    assert len(results) == 1


@pytest.mark.skip(
    reason="gfm-parity: ] in alt text breaks match"
)
def test_image_alt_text_with_bracket():
    """GFM handles escaped ] in alt text."""
    text = r"![alt \] text](https://img.com/pic.png)"
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://img.com/pic.png"


@pytest.mark.skip(
    reason="gfm-parity: escaped quote in title truncates match"
)
def test_image_escaped_quote_in_title():
    r"""GFM handles \" inside double-quoted titles."""
    text = r'![alt](https://img.com/pic.png "title \" here")'
    results = InlineImage.extract(text)
    assert len(results) == 1
    assert results[0].title == r'title " here'
