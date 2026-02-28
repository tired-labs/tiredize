# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.reference import ImageReference
from tiredize.markdown.types.reference import LinkReference
from tiredize.markdown.types.reference import ReferenceDefinition


# ===================================================================
#  ReferenceDefinition -- basic extraction
# ===================================================================


def test_reference_definition_basic():
    text = "[homepage]: https://example.com"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].text == "homepage"
    assert results[0].url == "https://example.com"
    assert results[0].title is None


def test_reference_definition_with_title():
    text = '[homepage]: https://example.com "My Homepage"'
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].title == "My Homepage"


def test_reference_definition_with_hash():
    text = "[anchor]: #some-section"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].url == "#some-section"


def test_reference_definition_with_relative_path():
    text = "[readme]: ./docs/README.md"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].url == "./docs/README.md"


def test_reference_definition_multiple():
    text = "[a]: https://a.com\n[b]: https://b.com"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 2
    assert results[0].text == "a"
    assert results[1].text == "b"


def test_reference_definition_no_matches():
    text = "Just plain text, no reference definitions."
    results = ReferenceDefinition.extract(text)
    assert len(results) == 0


def test_reference_definition_position():
    text = "[ref]: https://example.com"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].position == Position(offset=0, length=len(text))


def test_reference_definition_base_offset():
    text = "[ref]: https://example.com"
    results = ReferenceDefinition.extract(text, base_offset=50)
    assert len(results) == 1
    assert results[0].position.offset == 50


# ===================================================================
#  ReferenceDefinition -- sanitize
# ===================================================================


def test_reference_definition_sanitize_preserves_length():
    text = "[ref]: https://example.com\nMore text"
    sanitized = ReferenceDefinition.sanitize(text)
    assert len(sanitized) == len(text)
    assert "https://example.com" not in sanitized


def test_reference_definition_sanitize_idempotent():
    text = "[ref]: https://example.com\nMore text"
    first = ReferenceDefinition.sanitize(text)
    second = ReferenceDefinition.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# ===================================================================
#  ReferenceDefinition -- syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: indented reference definitions not supported"
)
def test_reference_definition_indented():
    """GFM allows 1-3 spaces before reference definitions."""
    text = "   [ref]: https://example.com"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].url == "https://example.com"


@pytest.mark.skip(reason="gfm-parity: URLs without #/./ characters rejected")
def test_reference_definition_url_without_special_chars():
    """GFM allows any URL in reference definitions."""
    text = "[ref]: example"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].url == "example"


@pytest.mark.skip(reason="gfm-parity: single-quote titles not supported")
def test_reference_definition_single_quote_title():
    """GFM allows single-quote titles in reference definitions."""
    text = "[ref]: https://example.com 'A Title'"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].title == "A Title"


# ===================================================================
#  LinkReference -- basic extraction
# ===================================================================


def test_link_reference_full():
    text = "[click here][homepage]"
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].text == "click here"
    assert results[0].reference == "homepage"


def test_link_reference_shortcut():
    """Shortcut reference: [ref] with no second bracket pair."""
    text = "[homepage]"
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].reference == "homepage"
    assert results[0].text is None


def test_link_reference_multiple():
    text = "[a][ref-a] and [b][ref-b]"
    results = LinkReference.extract(text)
    assert len(results) == 2


def test_link_reference_no_matches():
    text = "No references here."
    results = LinkReference.extract(text)
    assert len(results) == 0


def test_link_reference_position():
    text = "See [link][ref] for details."
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].position.offset == 4


def test_link_reference_base_offset():
    text = "[link][ref]"
    results = LinkReference.extract(text, base_offset=75)
    assert len(results) == 1
    assert results[0].position.offset == 75


def test_link_reference_not_confused_with_inline_link():
    """[text](url) should not match as a LinkReference (negative lookahead)."""
    text = "[link](https://example.com)"
    results = LinkReference.extract(text)
    assert len(results) == 0


def test_link_reference_not_confused_with_definition():
    """[ref]: url should not match as a LinkReference (negative lookahead)."""
    text = "[ref]: https://example.com"
    results = LinkReference.extract(text)
    assert len(results) == 0


def test_link_reference_not_image():
    """![alt][ref] should not match as LinkReference (negative lookbehind)."""
    text = "![alt][ref]"
    results = LinkReference.extract(text)
    assert len(results) == 0


# ===================================================================
#  LinkReference -- sanitize
# ===================================================================


def test_link_reference_sanitize_preserves_length():
    text = "See [text][ref] for more."
    sanitized = LinkReference.sanitize(text)
    assert len(sanitized) == len(text)
    assert "[text][ref]" not in sanitized


def test_link_reference_sanitize_idempotent():
    text = "See [text][ref] for more."
    first = LinkReference.sanitize(text)
    second = LinkReference.sanitize(first)
    assert first == second


# ===================================================================
#  LinkReference -- syntax variant tests (GFM spec compliance)
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: collapsed reference [text][] not handled correctly"
)
def test_link_reference_collapsed():
    """GFM collapsed reference [text][] should set text and reference
    to the same value."""
    text = "[homepage][]"
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].text == "homepage"
    assert results[0].reference == "homepage"


def test_link_reference_after_image_captures():
    """[ref] after ![img](a.png) is a valid link reference.
    The [ is preceded by ), not ] or !, so lookbehind correctly allows it."""
    text = "![img](a.png)[ref]"
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].reference == "ref"


# ===================================================================
#  ImageReference -- basic extraction
# ===================================================================


def test_image_reference_full():
    text = "![kitten photo][cat-pic]"
    results = ImageReference.extract(text)
    assert len(results) == 1
    assert results[0].text == "kitten photo"
    assert results[0].reference == "cat-pic"


def test_image_reference_shortcut():
    """Shortcut: ![ref] with no second bracket pair."""
    text = "![cat-pic]"
    results = ImageReference.extract(text)
    assert len(results) == 1
    assert results[0].reference == "cat-pic"
    assert results[0].text is None


def test_image_reference_multiple():
    text = "![a][ref-a] and ![b][ref-b]"
    results = ImageReference.extract(text)
    assert len(results) == 2


def test_image_reference_no_matches():
    text = "No image references here."
    results = ImageReference.extract(text)
    assert len(results) == 0


def test_image_reference_position():
    text = "See ![alt][ref] in the text."
    results = ImageReference.extract(text)
    assert len(results) == 1
    assert results[0].position.offset == 4


def test_image_reference_base_offset():
    text = "![alt][ref]"
    results = ImageReference.extract(text, base_offset=30)
    assert len(results) == 1
    assert results[0].position.offset == 30


# ===================================================================
#  ImageReference -- sanitize
# ===================================================================


def test_image_reference_sanitize_preserves_length():
    text = "See ![alt][ref] here."
    sanitized = ImageReference.sanitize(text)
    assert len(sanitized) == len(text)
    assert "![alt][ref]" not in sanitized


def test_image_reference_sanitize_idempotent():
    text = "See ![alt][ref] here."
    first = ImageReference.sanitize(text)
    second = ImageReference.sanitize(first)
    assert first == second


# ===================================================================
#  ImageReference -- syntax variant tests (GFM spec compliance)
# ===================================================================


def test_image_reference_preceded_by_bracket():
    """![alt][ref] preceded by ] is still a valid image reference.
    The lookbehind (?<!(\\])) checks the char before !, which is ],
    but this lookbehind is effectively a no-op since it tests !
    (the literal) not the preceding context character."""
    text = "]![alt][ref]"
    results = ImageReference.extract(text)
    assert len(results) == 1


# ===================================================================
#  Cross-type: references not extracted from code blocks
# ===================================================================


def test_reference_definition_not_inside_code_block():
    text = "```\n[ref]: https://example.com\n```"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 0


def test_link_reference_not_inside_code_block():
    text = "```\n[text][ref]\n```"
    results = LinkReference.extract(text)
    assert len(results) == 0


def test_image_reference_not_inside_code_block():
    text = "```\n![alt][ref]\n```"
    results = ImageReference.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-type: references inside inline code
#  ReferenceDefinition/LinkReference/ImageReference do NOT sanitize
#  CodeInline. Verify whether false positives occur.
# ===================================================================


def test_reference_definition_inside_inline_code_not_matched():
    """Reference definitions inside inline code should not be extracted.
    The start-of-line anchor prevents matching here because ` precedes [."""
    text = "`[ref]: https://example.com`"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 0


@pytest.mark.skip(reason="LinkReference does not sanitize CodeInline")
def test_link_reference_not_inside_inline_code():
    """Link references inside inline code should not be extracted."""
    text = "`[text][ref]`"
    results = LinkReference.extract(text)
    assert len(results) == 0


@pytest.mark.skip(reason="ImageReference does not sanitize CodeInline")
def test_image_reference_not_inside_inline_code():
    """Image references inside inline code should not be extracted."""
    text = "`![alt][ref]`"
    results = ImageReference.extract(text)
    assert len(results) == 0


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_reference_definition_empty_string():
    assert ReferenceDefinition.extract("") == []


def test_link_reference_empty_string():
    assert LinkReference.extract("") == []


def test_image_reference_empty_string():
    assert ImageReference.extract("") == []


def test_reference_definition_single_char():
    assert ReferenceDefinition.extract("[") == []


def test_link_reference_single_char():
    assert LinkReference.extract("[") == []


def test_image_reference_single_char():
    assert ImageReference.extract("!") == []


# ===================================================================
#  State mutation
# ===================================================================


def test_reference_definition_extract_does_not_mutate_input():
    text = "[ref]: https://example.com"
    original = text
    ReferenceDefinition.extract(text)
    assert text == original


def test_link_reference_extract_does_not_mutate_input():
    text = "[text][ref]"
    original = text
    LinkReference.extract(text)
    assert text == original


def test_image_reference_extract_does_not_mutate_input():
    text = "![alt][ref]"
    original = text
    ImageReference.extract(text)
    assert text == original


# ===================================================================
#  Unicode and non-ASCII
# ===================================================================


def test_reference_definition_unicode():
    text = "[café]: https://example.com/café"
    results = ReferenceDefinition.extract(text)
    assert len(results) == 1
    assert results[0].text == "café"
    assert "café" in results[0].url


def test_link_reference_unicode():
    text = "[crème brûlée][dessert]"
    results = LinkReference.extract(text)
    assert len(results) == 1
    assert results[0].text == "crème brûlée"


def test_image_reference_unicode():
    text = "![日本語テスト][photo]"
    results = ImageReference.extract(text)
    assert len(results) == 1
    assert results[0].text == "日本語テスト"
