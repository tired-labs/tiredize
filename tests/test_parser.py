from pathlib import Path
from tiredize.markdown.models.image import InlineImage
from tiredize.markdown.models.link import BareLink
from tiredize.markdown.models.link import InlineLink
from tiredize.markdown.parser import Parser
import datetime
import typing


def test_good_frontmatter_and_markdown():
    test_dir: Path = Path(__file__).parent / "test-cases"
    test_file = test_dir / "good-frontmatter-and-markdown.md"
    parser = Parser.from_path(test_file)

    # Frontmatter
    expected_frontmatter = {  # type: ignore
        'id': 'MD-001',
        'description': 'Valid Markdown document for parser testing.',
        'elements': [
            'frontmatter',
            'lists',
            'markdown',
            'sections',
            'tables'
        ],
        'tags': ['markdown', 'testing', 'tiredize'],
        'pub_date': datetime.date(1970, 1, 1)
    }
    assert parser.frontmatter_yaml is not None
    assert parser.frontmatter_yaml == expected_frontmatter

    # Fenced Lines
    expected_fenced_lines = {
        60, 61, 62, 63, 64, 65, 66, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79,
        80, 81, 82
    }
    assert len(parser.fenced_lines) == len(expected_fenced_lines)
    assert parser.fenced_lines == expected_fenced_lines

    # Sections
    assert len(parser.sections) == 18

    expected_sections: list[dict[typing.Any, typing.Any]] = [
        {
            'title': 'H1 Title: Markdown Feature Coverage',
            'level': 1,
            'images_inline': [],
            'images_reference': [],
            'line_start': 1,
            'line_end': 19,
            'links_bare': [
                BareLink(
                    end=493,
                    start=460,
                    url='https://example.com/autolink-test'
                )
            ],
            'links_inline': [
                InlineLink(
                    end=345,
                    start=301,
                    title='TIRED Labs',
                    url='https://example.com/tired-labs'
                )
            ],
            'reference_definitions': [],
            'links_reference': [
                {
                    "end": 256,
                    "start": 243,
                    "definition": 'local file',
                    "text": None
                }, {
                    "end": 399,
                    "start": 363,
                    "definition": 'ref-example',
                    "text": "reference style link"
                }
            ]
        }, {
            'title': 'H2 Section: Lists and Images',
            'level': 2,
            'images_inline': [],
            'images_reference': [],
            'line_start': 20,
            'line_end': 21,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'Unordered list',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 22,
            'line_end': 27,
            'links_bare': [],
            'links_inline': [
                InlineLink(
                    end=82,
                    start=54,
                    title='GitHub',
                    url='https://github.com'
                )
            ],
            'reference_definitions': [],
            'links_reference': [
                {
                    "end": 207,
                    "start": 179,
                    "definition": 'ref-example',
                    "text": "project site"
                }
            ]
        }, {
            'title': 'Ordered list',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 28,
            'line_end': 35,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'Images',
            'level': 3,
            'line_start': 36,
            'line_end': 48,
            'links_bare': [],
            'images_inline': [
                InlineImage(
                    alt_text="TIRED Logo - Inline",
                    end=113,
                    start=27,
                    title_text="TIRED Logo",
                    url="https://avatars.githubusercontent.com/u/235505457"
                )
            ],
            'images_reference': [
                {
                    "end": 181,
                    "start": 139,
                    "definition": 'img-logo',
                    "text": "TIRED Logo - Reference style"
                }
            ],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H2 Section: Blockquotes and Code',
            'level': 2,
            'images_inline': [],
            'images_reference': [],
            'line_start': 49,
            'line_end': 50,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Subsection: Blockquote',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 51,
            'line_end': 55,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Subsection: Fenced Code Blocks',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 56,
            'line_end': 83,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H2 Section: Tables',
            'level': 2,
            'images_inline': [],
            'images_reference': [],
            'line_start': 84,
            'line_end': 85,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Simple Table',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 86,
            'line_end': 92,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Table With Inline Code And Escaped Pipes',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 93,
            'line_end': 100,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Alignment Variants',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 101,
            'line_end': 109,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H2 Section: Headings Up To Level 6',
            'level': 2,
            'images_inline': [],
            'images_reference': [],
            'line_start': 110,
            'line_end': 111,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H3 Heading Level 3',
            'level': 3,
            'images_inline': [],
            'images_reference': [],
            'line_start': 112,
            'line_end': 115,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H4 Heading Level 4',
            'level': 4,
            'images_inline': [],
            'images_reference': [],
            'line_start': 116,
            'line_end': 119,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H5 Heading Level 5',
            'level': 5,
            'images_inline': [],
            'images_reference': [],
            'line_start': 120,
            'line_end': 123,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H6 Heading Level 6',
            'level': 6,
            'images_inline': [],
            'images_reference': [],
            'line_start': 124,
            'line_end': 129,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [],
            'links_reference': []
        }, {
            'title': 'H2 Section: Mixed Content',
            'level': 2,
            'images_inline': [],
            'images_reference': [],
            'line_start': 130,
            'line_end': 145,
            'links_bare': [],
            'links_inline': [],
            'reference_definitions': [
                {
                    "end": 260,
                    "start": 243,
                    "title": 'images',
                    "url": '#images'
                }, {
                    "end": 322,
                    "start": 261,
                    "title": 'img-logo',
                    "url": 'https://avatars.githubusercontent.com/u/235505457'
                }, {
                    "end": 354,
                    "start": 323,
                    "title": 'local file',
                    "url": '../test_parser.py'
                }, {
                    "end": 400,
                    "start": 355,
                    "title": 'ref-example',
                    "url": 'https://github.com/tired-labs/'
                }
            ],
            'links_reference': [
                {
                    "end": 113,
                    "start": 72,
                    "definition": 'images',
                    "text": "shortcut to the images section"
                }
            ]
        },
    ]

    for i, expected in enumerate(expected_sections, start=0):
        actual = parser.sections[i]
        assert expected["title"] == actual.header_title
        assert expected["level"] == actual.header_level
        assert expected["line_start"] == actual.line_start
        assert expected["line_end"] == actual.line_end
        assert expected["links_inline"] == actual.links_inline

        assert len(expected["reference_definitions"]) == \
            len(actual.reference_definitions)
        for j, exp_ref_def in enumerate(
                expected["reference_definitions"]):
            act_ref_def = actual.reference_definitions[j]
            assert exp_ref_def["end"] == act_ref_def.end
            assert exp_ref_def["start"] == act_ref_def.start
            assert exp_ref_def["title"] == act_ref_def.title
            assert exp_ref_def["url"] == act_ref_def.url

        assert len(expected["links_reference"]) == \
            len(actual.links_reference)
        for j, exp_link_refs in enumerate(
                expected["links_reference"]):
            act_link_refs = actual.links_reference[j]
            act_ref_def = act_link_refs.definition
            assert exp_link_refs["definition"] == act_ref_def.title
            assert exp_link_refs["text"] == act_link_refs.text
            assert exp_link_refs["start"] == act_link_refs.start
            assert exp_link_refs["end"] == act_link_refs.end

        assert len(expected["images_reference"]) == \
            len(actual.images_reference)
        for j, exp_image_refs in enumerate(
                expected["images_reference"]):
            act_image_refs = actual.images_reference[j]
            act_ref_def = act_image_refs.definition
            assert exp_image_refs["definition"] == act_ref_def.title
            assert exp_image_refs["text"] == act_image_refs.text
            assert exp_image_refs["start"] == act_image_refs.start
            assert exp_image_refs["end"] == act_image_refs.end

        assert len(expected["images_inline"]) == \
            len(actual.images_inline)
        for j, exp_images in enumerate(
                expected["images_inline"]):
            act_images = actual.images_inline[j]
            assert exp_images == act_images

        assert len(expected["links_bare"]) == \
            len(actual.links_bare)
        for j, exp_links in enumerate(
                expected["links_bare"]):
            act_links = actual.links_bare[j]
            assert exp_links == act_links
