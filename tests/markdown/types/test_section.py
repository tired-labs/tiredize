# Standard library
from __future__ import annotations

# Local
from tiredize.markdown.types.section import Section


def test_flat_siblings_no_nesting():
    md = "## Alpha\n\n## Bravo\n\n## Charlie\n"
    sections = Section.extract(md)

    assert len(sections) == 3
    assert sections[0].header.title == "Alpha"
    assert sections[1].header.title == "Bravo"
    assert sections[2].header.title == "Charlie"
    assert sections[0].subsections == []
    assert sections[1].subsections == []
    assert sections[2].subsections == []


def test_simple_parent_child():
    md = "# Parent\n\n## Child\n"
    sections = Section.extract(md)

    assert len(sections) == 2
    assert sections[0].header.title == "Parent"
    assert len(sections[0].subsections) == 1
    assert sections[0].subsections[0].header.title == "Child"
    assert sections[1].subsections == []


def test_parent_with_multiple_children():
    md = "# Parent\n\n## Alice\n\n## Bob\n\n## Carol\n"
    sections = Section.extract(md)

    assert len(sections) == 4
    assert sections[0].header.title == "Parent"
    assert len(sections[0].subsections) == 3
    assert sections[0].subsections[0].header.title == "Alice"
    assert sections[0].subsections[1].header.title == "Bob"
    assert sections[0].subsections[2].header.title == "Carol"


def test_grandchildren_do_not_leak_to_grandparent():
    md = (
        "# Grandparent\n\n"
        "## Parent\n\n"
        "### Grandchild\n\n"
        "## Sibling\n"
    )
    sections = Section.extract(md)

    assert len(sections) == 4

    grandparent = sections[0]
    assert grandparent.header.title == "Grandparent"
    assert len(grandparent.subsections) == 2
    assert grandparent.subsections[0].header.title == "Parent"
    assert grandparent.subsections[1].header.title == "Sibling"

    parent = sections[1]
    assert parent.header.title == "Parent"
    assert len(parent.subsections) == 1
    assert parent.subsections[0].header.title == "Grandchild"


def test_deep_nesting():
    md = (
        "# Level One\n\n"
        "## Level Two\n\n"
        "### Level Three\n\n"
        "#### Level Four\n"
    )
    sections = Section.extract(md)

    assert len(sections) == 4

    lvl1 = sections[0]
    assert len(lvl1.subsections) == 1
    assert lvl1.subsections[0].header.title == "Level Two"

    lvl2 = sections[1]
    assert len(lvl2.subsections) == 1
    assert lvl2.subsections[0].header.title == "Level Three"

    lvl3 = sections[2]
    assert len(lvl3.subsections) == 1
    assert lvl3.subsections[0].header.title == "Level Four"

    lvl4 = sections[3]
    assert lvl4.subsections == []


def test_skipped_levels():
    md = "# Root\n\n### Skipped To Three\n"
    sections = Section.extract(md)

    assert len(sections) == 2

    root = sections[0]
    assert len(root.subsections) == 1
    assert root.subsections[0].header.title == "Skipped To Three"

    assert sections[1].subsections == []


def test_table_inside_code_block_not_extracted():
    """Tables inside code fences must not appear in section.tables."""
    md = (
        "# Spell Components\n\n"
        "Here is an example table:\n\n"
        "```markdown\n"
        "| Ingredient | Quantity |\n"
        "|------------|----------|\n"
        "| Bat wings  | 3        |\n"
        "```\n"
    )
    sections = Section.extract(md)
    assert len(sections) == 1
    assert sections[0].tables == []


# --- No headers in text (lines 51-60) ---


def test_no_headers_creates_single_section():
    """Text with no headers produces one section with level-0 header."""
    md = "Just a paragraph.\n\nAnother paragraph.\n"
    sections = Section.extract(md)

    assert len(sections) == 1
    assert sections[0].header.level == 0
    assert sections[0].header.title == ""
    assert sections[0].position.offset == 0
    assert sections[0].position.length == len(md)
    assert sections[0].string == md


def test_no_headers_level_zero_breaks_map_subsections():
    """Level-0 headers cause _map_subsections to break (line 167).
    Verify no subsections are created for level-0 sections."""
    md = "No headers here."
    sections = Section.extract(md)
    assert len(sections) == 1
    assert sections[0].subsections == []


# --- Section._extract with no header (line 93) ---


def test_extract_text_without_header():
    """Text without a header at the start gets a dummy level-0 header."""
    md = "Paragraph text without any header."
    sections = Section.extract(md)
    assert len(sections) == 1
    assert sections[0].header.level == 0
    assert sections[0].header.slug == ""


# --- Idempotency ---


def test_extract_idempotent():
    md = "# Alpha\n\n## Bravo\n\n# Charlie\n"
    first = Section.extract(md)
    second = Section.extract(md)
    assert len(first) == len(second)
    for a, b in zip(first, second):
        assert a.header.title == b.header.title
        assert a.position == b.position


# --- State mutation ---


def test_extract_does_not_mutate_input():
    md = "# Title\n\nBody text.\n"
    original = md
    Section.extract(md)
    assert md == original


# --- Boundary inputs ---


def test_extract_empty_string():
    sections = Section.extract("")
    assert len(sections) == 1
    assert sections[0].header.level == 0


def test_extract_single_char():
    sections = Section.extract("x")
    assert len(sections) == 1


# --- Unicode ---


def test_extract_unicode_content():
    md = "# Résumé\n\nCafé text with 日本語.\n"
    sections = Section.extract(md)
    assert len(sections) == 1
    assert sections[0].header.title == "Résumé"
