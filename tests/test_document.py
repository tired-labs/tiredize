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
    expected_sections: typing.List[Position] = [
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

    expected_headers: typing.List[Position] = [
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

    for i, section in enumerate(document.sections):
        assert section.position == expected_sections[i]
        assert section.header.position == expected_headers[i]
