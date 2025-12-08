from pathlib import Path
from tiredize.markdown.types.document import Document
from tiredize.markdown.types.header import Header
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
    expected_headers: typing.List[Header] = []
    expected_headers.append(
        Header(
            level=1,
            position=Position(line=1, offset=0, length=37),
            string="# H1 Title: Markdown Feature Coverage",
            title="H1 Title: Markdown Feature Coverage",
        )
    )
    expected_headers.append(
        Header(
            string="## H2 Section: Lists and Images",
            level=2,
            position=Position(line=20, offset=0, length=31),
            title="H2 Section: Lists and Images",
        )
    )
    expected_headers.append(
        Header(
            string="### Unordered list",
            level=3,
            position=Position(line=22, offset=0, length=18),
            title="Unordered list",
        )
    )
    expected_headers.append(
        Header(
            string="### Ordered list",
            level=3,
            position=Position(line=28, offset=0, length=16),
            title="Ordered list",
        )
    )
    expected_headers.append(
        Header(
            string="### Images",
            level=3,
            position=Position(line=36, offset=0, length=10),
            title="Images",
        )
    )
    expected_headers.append(
        Header(
            string="## H2 Section: Blockquotes and Code",
            level=2,
            position=Position(line=49, offset=0, length=35),
            title="H2 Section: Blockquotes and Code",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Subsection: Blockquote",
            level=3,
            position=Position(line=51, offset=0, length=29),
            title="H3 Subsection: Blockquote",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Subsection: Fenced Code Blocks",
            level=3,
            position=Position(line=56, offset=0, length=37),
            title="H3 Subsection: Fenced Code Blocks",
        )
    )
    expected_headers.append(
        Header(
            string="## H2 Section: Tables",
            level=2,
            position=Position(line=84, offset=0, length=21),
            title="H2 Section: Tables",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Simple Table",
            level=3,
            position=Position(line=86, offset=0, length=19),
            title="H3 Simple Table",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Table With Inline Code And Escaped Pipes",
            level=3,
            position=Position(line=93, offset=0, length=47),
            title="H3 Table With Inline Code And Escaped Pipes",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Alignment Variants",
            level=3,
            position=Position(line=101, offset=0, length=25),
            title="H3 Alignment Variants",
        )
    )
    expected_headers.append(
        Header(
            string="## H2 Section: Headings Up To Level 6",
            level=2,
            position=Position(line=110, offset=0, length=37),
            title="H2 Section: Headings Up To Level 6",
        )
    )
    expected_headers.append(
        Header(
            string="### H3 Heading Level 3",
            level=3,
            position=Position(line=112, offset=0, length=22),
            title="H3 Heading Level 3",
        )
    )
    expected_headers.append(
        Header(
            string="#### H4 Heading Level 4",
            level=4,
            position=Position(line=116, offset=0, length=23),
            title="H4 Heading Level 4",
        )
    )
    expected_headers.append(
        Header(
            string="##### H5 Heading Level 5",
            level=5,
            position=Position(line=120, offset=0, length=24),
            title="H5 Heading Level 5",
        )
    )
    expected_headers.append(
        Header(
            string="###### H6 Heading Level 6",
            level=6,
            position=Position(line=124, offset=0, length=25),
            title="H6 Heading Level 6",
        )
    )
    expected_headers.append(
        Header(
            string="## H2 Section: Mixed Content",
            level=2,
            position=Position(line=130, offset=0, length=28),
            title="H2 Section: Mixed Content",
        )
    )

    for i, section in enumerate(document.sections):
        assert section.header == expected_headers[i]
