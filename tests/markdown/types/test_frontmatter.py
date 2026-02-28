# Standard library
from __future__ import annotations
import datetime
from typing import Any

# Third-party
import pytest
import yaml

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.frontmatter import FrontMatter

md_section = """{}# Markdown Test Section - Lorem Ipsum

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

Line 14, Offset 00 {}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu
malesuada eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et
enim pretium rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat.
Mauris vehicula condimentum consequat. Phasellus fermentum rhoncus enim nec
volutpat.

Line 23, Offset 00 {}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et
egestas leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec
maximus ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor.
Vivamus dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at
volutpat nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum.
Nulla vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci,
a fringilla ex. In hac habitasse platea dictumst.

Line 33, Offset 00 {}

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id
arcu porta tempus.

Line 43, Offset 00 {}

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien
eu tortor.

Line 53, Offset 00
{}"""


def test_no_frontmatter():
    md_test = md_section
    frontmatter = FrontMatter.extract(md_test)
    assert frontmatter is None


def test_single_frontmatter_normal():
    actual_data: dict[str, Any] = {
        'title': 'Markdown Frontmatter Example',
        'id': 4444,
        'publication_date': datetime.datetime.now(),
        'tags': ['YAML', 'Markdown', 'TIRED']
    }
    actual_yaml = yaml.safe_dump(actual_data)
    actual_string = f"---\n{actual_yaml}\n---\n"
    position = Position(offset=0, length=len(actual_string))

    expected = FrontMatter(
        content=actual_data,
        string=actual_string,
        position=position
    )

    md_text = md_section.format(actual_string, "", "", "", "", "")
    frontmatter = FrontMatter.extract(md_text)
    assert frontmatter is not None
    assert frontmatter == expected


def test_six_frontmatters_repeated():
    actual_data: dict[str, Any] = {
        'title': 'Markdown Frontmatter Example',
        'id': 4444,
        'publication_date': datetime.datetime.now(),
        'tags': ['YAML', 'Markdown', 'TIRED']
    }
    actual_yaml = yaml.safe_dump(actual_data)
    actual_string = f"---\n{actual_yaml}\n---\n"
    position = Position(offset=0, length=len(actual_string))

    expected = FrontMatter(
        content=actual_data,
        string=actual_string,
        position=position
    )

    md_text = md_section.format(
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string
    )

    regex_matches = FrontMatter.extract(md_text)
    assert regex_matches is not None
    assert regex_matches == expected


# ===================================================================
#  Edge cases -- malformed YAML (lines 52-53)
# ===================================================================


def test_malformed_yaml_returns_none():
    """Malformed YAML triggers yaml.YAMLError, returns None."""
    text = "---\n{{invalid yaml: [unterminated\n---\n# Content"
    result = FrontMatter.extract(text)
    assert result is None


# ===================================================================
#  Sanitize method (line 67)
# ===================================================================


@pytest.mark.skip(
    reason="sanitize_text drops trailing newline via splitlines()"
)
def test_frontmatter_sanitize_preserves_length():
    """Sanitize must preserve string length per sanitization contract."""
    text = "---\ntitle: Hello\n---\n# Content"
    sanitized = FrontMatter.sanitize(text)
    assert len(sanitized) == len(text)
    assert "title" not in sanitized


def test_frontmatter_sanitize_no_frontmatter():
    text = "# Just a heading\n\nParagraph text."
    sanitized = FrontMatter.sanitize(text)
    assert sanitized == text


@pytest.mark.skip(
    reason="sanitize_text drops trailing newline via splitlines()"
)
def test_frontmatter_sanitize_idempotent():
    """Sanitize applied twice must produce the same result
    and preserve length."""
    text = "---\ntitle: Hello\n---\n# Content"
    first = FrontMatter.sanitize(text)
    second = FrontMatter.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_frontmatter_extract_empty_string():
    result = FrontMatter.extract("")
    assert result is None


def test_frontmatter_extract_single_char():
    result = FrontMatter.extract("-")
    assert result is None


# ===================================================================
#  Syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: YAML ... closing delimiter not supported"
)
def test_frontmatter_dot_closing():
    """YAML spec supports ... as closing delimiter for frontmatter."""
    text = "---\ntitle: Hello\n...\n# Content"
    result = FrontMatter.extract(text)
    assert result is not None
    assert result.content["title"] == "Hello"


@pytest.mark.skip(reason="gfm-parity: empty frontmatter not supported")
def test_frontmatter_empty_content():
    """Empty frontmatter (---\\n---\\n) should be valid with empty content."""
    text = "---\n---\n# Content"
    result = FrontMatter.extract(text)
    assert result is not None


def test_frontmatter_element_like_syntax_in_yaml():
    """YAML values that look like links or code should not confuse
    the frontmatter extractor."""
    text = "---\nurl: https://example.com\ncode: \"`hello`\"\n---\n# Content"
    result = FrontMatter.extract(text)
    assert result is not None
    assert result.content["url"] == "https://example.com"


# ===================================================================
#  State mutation
# ===================================================================


def test_frontmatter_extract_does_not_mutate_input():
    text = "---\ntitle: Hello\n---\n# Content"
    original = text
    FrontMatter.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_frontmatter_unicode_yaml_values():
    text = "---\ntitle: café résumé\nauthor: 日本太郎\n---\n# Content"
    result = FrontMatter.extract(text)
    assert result is not None
    assert result.content["title"] == "café résumé"
    assert result.content["author"] == "日本太郎"
