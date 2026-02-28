# Standard library
from __future__ import annotations
import datetime
from pathlib import Path
from typing import Any

# Third-party
import yaml

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.document import Document


def test_document_no_path_or_string():
    document = Document()
    try:
        document.load()
    except ValueError as e:
        assert str(e) == "Provide either 'path' or 'text'."


def test_document_both_path_and_string():
    document = Document()
    try:
        document.load(Path("fakefile.md"), "Some markdown text")
    except ValueError as e:
        assert str(e) == "Provide either 'path' or 'text', not both."


def test_document_load_nonexistent_path():
    document = Document()
    try:
        document.load(path=Path("the/cake/is/a/lie.md"))
        assert False, "Expected FileNotFoundError was not raised"
    except FileNotFoundError:
        pass


def test_document_load_from_string():
    md_text = r"""# Sample Document

    This is a sample markdown document.
"""

    document = Document()
    document.load(text=md_text)
    assert document.string == md_text
    assert document.frontmatter is None


def test_document_load_from_path():
    document = Document()
    test_path = r"./tests/test_cases/markdown/good-frontmatter-and-markdown.md"
    document.load(Path(test_path))

    assert document.frontmatter is not None
    expected_data: dict[str, Any] = {
        'id': 'MD-001',
        'description': "Valid Markdown document for parser testing.",
        'elements': ['frontmatter', 'lists', 'markdown', 'sections', 'tables'],
        'tags': ['markdown', 'testing', 'tiredize'],
        'pub_date': datetime.date(1970, 1, 1)
    }
    expected_yaml = yaml.safe_dump(expected_data)
    expected_string = f"---\n{expected_yaml}---\n"
    expected_pos = Position(offset=0, length=len(expected_string))
    assert document.frontmatter.content == expected_data
    assert document.frontmatter.position == expected_pos

    assert len(document.sections) == 18
    expected_section: list[Position] = [
        Position(offset=199, length=636),
        Position(offset=835, length=33),
        Position(offset=868, length=209),
        Position(offset=1077, length=166),
        Position(offset=1243, length=187),
        Position(offset=1430, length=37),
        Position(offset=1467, length=152),
        Position(offset=1619, length=492),
        Position(offset=2111, length=23),
        Position(offset=2134, length=118),
        Position(offset=2252, length=320),
        Position(offset=2572, length=209),
        Position(offset=2781, length=39),
        Position(offset=2820, length=56),
        Position(offset=2876, length=57),
        Position(offset=2933, length=58),
        Position(offset=2991, length=64),
        Position(offset=3055, length=401)
    ]

    expected_header: list[Position] = [
        Position(offset=199, length=37),
        Position(offset=835, length=31),
        Position(offset=868, length=18),
        Position(offset=1077, length=16),
        Position(offset=1243, length=10),
        Position(offset=1430, length=35),
        Position(offset=1467, length=29),
        Position(offset=1619, length=37),
        Position(offset=2111, length=21),
        Position(offset=2134, length=19),
        Position(offset=2252, length=47),
        Position(offset=2572, length=25),
        Position(offset=2781, length=37),
        Position(offset=2820, length=22),
        Position(offset=2876, length=23),
        Position(offset=2933, length=24),
        Position(offset=2991, length=25),
        Position(offset=3055, length=28)
    ]

    expected_code_block: list[list[Position]]
    expected_code_block = [[] for _ in range(18)]
    expected_code_block[7] = [
        Position(offset=1688, length=142),
        Position(offset=1880, length=229)
    ]

    expected_code_inline: list[list[Position]]
    expected_code_inline = [[] for _ in range(18)]
    expected_code_inline[0] = [Position(offset=814, length=13)]
    expected_code_inline[2] = [Position(offset=980, length=22)]
    expected_code_inline[3] = [Position(offset=1211, length=6)]
    expected_code_inline[10] = [
        Position(offset=2411, length=19),
        Position(offset=2465, length=4),
        Position(offset=2519, length=8)
    ]
    expected_code_inline[17] = [Position(offset=3242, length=20)]

    expected_link_bare: list[list[Position]]
    expected_link_bare = [[] for _ in range(18)]
    expected_link_bare[0] = [Position(offset=659, length=33)]

    expected_link_bracket: list[list[Position]]
    expected_link_bracket = [[] for _ in range(18)]
    expected_link_bracket[0] = [Position(offset=726, length=32)]

    expected_link_inline: list[list[Position]]
    expected_link_inline = [[] for _ in range(18)]
    expected_link_inline[0] = [Position(offset=500, length=44)]
    expected_link_inline[2] = [Position(offset=922, length=28)]

    expected_link_reference: list[list[Position]]
    expected_link_reference = [[] for _ in range(18)]
    expected_link_reference[0] = [
        Position(offset=442, length=12),
        Position(offset=562, length=35)
    ]
    expected_link_reference[2] = [Position(offset=1047, length=27)]
    expected_link_reference[17] = [Position(offset=3127, length=40)]

    expected_image_inline: list[list[Position]]
    expected_image_inline = [[] for _ in range(18)]
    expected_image_inline[4] = [Position(offset=1270, length=86)]

    expected_quoteblock: list[list[Position]]
    expected_quoteblock = [[] for _ in range(18)]
    expected_quoteblock[6] = [Position(offset=1498, length=119)]

    expected_image_reference: list[list[Position]]
    expected_image_reference = [[] for _ in range(18)]
    expected_image_reference[4] = [Position(offset=1382, length=41)]

    expected_table: list[list[Position]]
    expected_table = [[] for _ in range(18)]
    expected_table[9] = [Position(offset=2155, length=96)]
    expected_table[10] = [Position(offset=2301, length=270)]
    expected_table[11] = [Position(offset=2599, length=176)]

    expected_reference_definition: list[list[Position]]
    expected_reference_definition = [[] for _ in range(18)]
    expected_reference_definition[17] = [
        Position(offset=3298, length=17),
        Position(offset=3316, length=61),
        Position(offset=3378, length=31),
        Position(offset=3410, length=45)
    ]

    for i, section in enumerate(document.sections):
        assert section.position == expected_section[i]
        assert section.header.position == expected_header[i]

        assert len(section.code_block) == len(expected_code_block[i])
        for j, code in enumerate(section.code_block):
            assert code.position == expected_code_block[i][j]

        assert len(section.code_inline) == len(expected_code_inline[i])
        for j, code in enumerate(section.code_inline):
            assert code.position == expected_code_inline[i][j]

        assert len(section.images_inline) == len(expected_image_inline[i])
        for j, image in enumerate(section.images_inline):
            assert image.position == expected_image_inline[i][j]

        assert len(section.images_reference) == len(
            expected_image_reference[i])
        for j, image in enumerate(section.images_reference):
            assert image.position == expected_image_reference[i][j]

        assert len(section.links_bare) == len(expected_link_bare[i])
        for j, link in enumerate(section.links_bare):
            assert link.position == expected_link_bare[i][j]

        assert len(section.links_bracket) == len(expected_link_bracket[i])
        for j, link in enumerate(section.links_bracket):
            assert link.position == expected_link_bracket[i][j]

        assert len(section.links_inline) == len(expected_link_inline[i])
        for j, link in enumerate(section.links_inline):
            assert link.position == expected_link_inline[i][j]

        assert len(section.links_reference) == len(expected_link_reference[i])
        for j, link in enumerate(section.links_reference):
            assert link.position == expected_link_reference[i][j]

        assert len(section.quoteblocks) == len(expected_quoteblock[i])
        for j, quoteblock in enumerate(section.quoteblocks):
            assert quoteblock.position == expected_quoteblock[i][j]

        assert len(section.reference_definitions) == len(
            expected_reference_definition[i])
        for j, reference in enumerate(section.reference_definitions):
            assert reference.position == expected_reference_definition[i][j]

        assert len(section.tables) == len(expected_table[i])
        for j, table in enumerate(section.tables):
            assert table.position == expected_table[i][j]


# --- line_col: bounds clamping (lines 43-51) ---


def test_line_col_basic():
    doc = Document()
    doc.load(text="Hello\nWorld\n")
    line, col = doc.line_col(0)
    assert line == 1
    assert col == 0


def test_line_col_second_line():
    doc = Document()
    doc.load(text="Hello\nWorld\n")
    line, col = doc.line_col(6)
    assert line == 2
    assert col == 0


def test_line_col_mid_line():
    doc = Document()
    doc.load(text="Hello\nWorld\n")
    line, col = doc.line_col(8)
    assert line == 2
    assert col == 2


def test_line_col_negative_offset():
    """Negative offset clamped to 0 (line 43-44)."""
    doc = Document()
    doc.load(text="Hello\nWorld\n")
    line, col = doc.line_col(-5)
    assert line == 1
    assert col == 0


def test_line_col_offset_beyond_length():
    """Offset beyond document length clamped to doc_len (lines 45-47)."""
    doc = Document()
    doc.load(text="Hello\nWorld\n")
    line, col = doc.line_col(9999)
    # Clamped to len("Hello\nWorld\n") = 12, which is line 3, col 0
    assert line == 3
    assert col == 0


def test_line_col_zero_length_document():
    """Edge case: document loaded with minimal content."""
    doc = Document()
    doc.load(text="x")
    line, col = doc.line_col(0)
    assert line == 1
    assert col == 0


# --- Document.load() called twice (state mutation) ---


def test_document_load_twice_replaces_state():
    """Second load() cleanly replaces state, not accumulates."""
    doc = Document()
    doc.load(text="# First\n\nParagraph.")
    assert len(doc.sections) >= 1
    first_sections = len(doc.sections)

    doc.load(text="# Second\n\nDifferent content.")
    assert len(doc.sections) >= 1
    assert doc.sections[0].header.title == "Second"
    # Confirm it didn't accumulate sections from first load
    assert len(doc.sections) == first_sections


# --- Unicode ---


def test_document_unicode_content():
    doc = Document()
    doc.load(text="# Café Guide\n\n日本語テキスト\n")
    assert len(doc.sections) == 1
    assert doc.sections[0].header.title == "Café Guide"
