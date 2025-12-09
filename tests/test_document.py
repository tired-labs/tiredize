from pathlib import Path
from tiredize.markdown.types.document import Document
from tiredize.types import Position
import datetime
import typing
import yaml


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
    test_path = r"./tests/test-cases/good-frontmatter-and-markdown.md"
    document.load(Path(test_path))

    assert document.frontmatter is not None
    expected_data: typing.Dict[str, typing.Any] = {
        'id': 'MD-001',
        'description': "Valid Markdown document for parser testing.",
        'elements': ['frontmatter', 'lists', 'markdown', 'sections', 'tables'],
        'tags': ['markdown', 'testing', 'tiredize'],
        'pub_date': datetime.date(1970, 1, 1)
    }
    expected_yaml = yaml.safe_dump(expected_data)
    expected_string = f"---\n{expected_yaml}---\n"
    expected_pos = Position(line=1, offset=0, length=len(expected_string))
    assert document.frontmatter.content == expected_data
    assert document.frontmatter.position == expected_pos

    assert len(document.sections) == 18
    expected_section: typing.List[Position] = [
        Position(line=1, offset=0, length=636),
        Position(line=20, offset=0, length=33),
        Position(line=22, offset=0, length=209),
        Position(line=28, offset=0, length=166),
        Position(line=36, offset=0, length=187),
        Position(line=49, offset=0, length=37),
        Position(line=51, offset=0, length=152),
        Position(line=56, offset=0, length=492),
        Position(line=84, offset=0, length=23),
        Position(line=86, offset=0, length=118),
        Position(line=93, offset=0, length=320),
        Position(line=101, offset=0, length=209),
        Position(line=110, offset=0, length=39),
        Position(line=112, offset=0, length=56),
        Position(line=116, offset=0, length=57),
        Position(line=120, offset=0, length=58),
        Position(line=124, offset=0, length=64),
        Position(line=130, offset=0, length=401)
    ]

    expected_header: typing.List[Position] = [
        Position(line=1, offset=0, length=37),
        Position(line=1, offset=0, length=31),
        Position(line=1, offset=0, length=18),
        Position(line=1, offset=0, length=16),
        Position(line=1, offset=0, length=10),
        Position(line=1, offset=0, length=35),
        Position(line=1, offset=0, length=29),
        Position(line=1, offset=0, length=37),
        Position(line=1, offset=0, length=21),
        Position(line=1, offset=0, length=19),
        Position(line=1, offset=0, length=47),
        Position(line=1, offset=0, length=25),
        Position(line=1, offset=0, length=37),
        Position(line=1, offset=0, length=22),
        Position(line=1, offset=0, length=23),
        Position(line=1, offset=0, length=24),
        Position(line=1, offset=0, length=25),
        Position(line=1, offset=0, length=28)
    ]

    expected_code_block: typing.List[typing.List[Position]]
    expected_code_block = [[] for _ in range(18)]
    expected_code_block[7] = [
        Position(line=5, offset=0, length=142),
        Position(line=15, offset=0, length=229)
    ]

    expected_code_inline: typing.List[typing.List[Position]]
    expected_code_inline = [[] for _ in range(18)]
    expected_code_inline[0] = [Position(line=16, offset=53, length=13)]
    expected_code_inline[2] = [Position(line=4, offset=28, length=22)]
    expected_code_inline[3] = [Position(line=6, offset=28, length=6)]
    expected_code_inline[10] = [
        Position(line=5, offset=2, length=19),
        Position(line=6, offset=2, length=4),
        Position(line=7, offset=2, length=8)
    ]
    expected_code_inline[17] = [Position(line=7, offset=72, length=20)]

    expected_link_bare: typing.List[typing.List[Position]]
    expected_link_bare = [[] for _ in range(18)]
    expected_link_bare[0] = [Position(line=12, offset=0, length=33)]

    expected_link_bracket: typing.List[typing.List[Position]]
    expected_link_bracket = [[] for _ in range(18)]
    expected_link_bracket[0] = [Position(line=14, offset=32, length=32)]

    expected_link_inline: typing.List[typing.List[Position]]
    expected_link_inline = [[] for _ in range(18)]
    expected_link_inline[0] = [Position(line=7, offset=43, length=44)]
    expected_link_inline[2] = [Position(line=3, offset=34, length=28)]

    expected_link_reference: typing.List[typing.List[Position]]
    expected_link_reference = [[] for _ in range(18)]
    expected_link_reference[0] = [
        Position(line=5, offset=52, length=12),
        Position(line=8, offset=55, length=35)
    ]
    expected_link_reference[2] = [Position(line=5, offset=43, length=27)]
    expected_link_reference[17] = [Position(line=5, offset=16, length=40)]

    expected_image_inline: typing.List[typing.List[Position]]
    expected_image_inline = [[] for _ in range(18)]
    expected_image_inline[4] = [Position(line=5, offset=0, length=86)]

    expected_quoteblock: typing.List[typing.List[Position]]
    expected_quoteblock = [[] for _ in range(18)]
    expected_quoteblock[6] = [Position(line=3, offset=0, length=119)]

    expected_image_reference: typing.List[typing.List[Position]]
    expected_image_reference = [[] for _ in range(18)]
    expected_image_reference[4] = [Position(line=10, offset=0, length=41)]

    expected_table: typing.List[typing.List[Position]]
    expected_table = [[] for _ in range(18)]
    expected_table[9] = [Position(line=3, offset=0, length=96)]
    expected_table[10] = [Position(line=3, offset=0, length=270)]
    expected_table[11] = [Position(line=3, offset=0, length=176)]

    expected_reference_definition: typing.List[typing.List[Position]]
    expected_reference_definition = [[] for _ in range(18)]
    expected_reference_definition[17] = [
        Position(line=13, offset=0, length=17),
        Position(line=14, offset=0, length=61),
        Position(line=15, offset=0, length=31),
        Position(line=16, offset=0, length=45)
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
