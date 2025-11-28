from pathlib import Path
import tempfile
from tiredize.document import Document, Table
import pytest

def test_frontmatter_good():
    test_markdown = r"""---
title: Example
tags:
    - one
    - two
---
# Title

Lorem Ipsum...

## Section One

Lorem Ipsum...

### Subsection One

Lorem Ipsum...

## Section Two

Lorem Ipsum...

### Subsection Two

Lorem Ipsum...
"""

    doc = Document.from_text(test_markdown)

    assert doc.front_matter == {
        "title": "Example",
        "tags": ["one", "two"],
    }
    assert doc.body == """
# Title

Lorem Ipsum...

## Section One

Lorem Ipsum...

### Subsection One

Lorem Ipsum...

## Section Two

Lorem Ipsum...

### Subsection Two

Lorem Ipsum...
"""
    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title"),
        (2, "Section One"),
        (3, "Subsection One"),
        (2, "Section Two"),
        (3, "Subsection Two"),
    ]


def test_frontmatter_preceding_newline():
    test_markdown = r"""
---
title: Example
tags:
    - one
    - two
---
# Heading 1

Body text.
"""

    doc = Document.from_text(test_markdown)

    assert doc.front_matter == {}
    assert doc.body == test_markdown


def test_frontmatter_missing_delimiter():
    test_markdown = r"""
---
title: Example
tags:
    - one
    - two
# Heading 1

Body text.
"""

    doc = Document.from_text(test_markdown)

    assert doc.front_matter == {}
    assert doc.body == test_markdown


def test_frontmatter_bad_yaml():
    test_markdown = r"""---
title: Example
tags: tags:
    - one
    - two
---
# Heading 1

Body text.
"""

    bad_yaml = """
title: Example
tags: tags:
    - one
    - two
"""

    with pytest.raises(ValueError) as err:
        Document.from_text(test_markdown)

    assert str(err.value) == "Invalid YAML in frontmatter: " + repr(bad_yaml)


def test_headings_are_parsed_with_levels_and_lines():
    test_markdown = r"""# Title

Lorem Ipsum...

## Section One

Lorem Ipsum...

### Subsection One

Lorem Ipsum...

## Section Two

Lorem Ipsum...

### Subsection Two

Lorem Ipsum...
"""

    doc = Document.from_text(test_markdown)
    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title"),
        (2, "Section One"),
        (3, "Subsection One"),
        (2, "Section Two"),
        (3, "Subsection Two"),
    ]


def test_fenced_lines_track_code_blocks():
    test_markdown = r"""# Title

```python
print("inside")
```
Outside
"""

    doc = Document.from_text(test_markdown)

    fenced = doc.fenced_lines
    assert len(fenced) == 3
    assert fenced == {3, 4, 5}

    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title")
    ]


def test_tables_are_extracted_with_header_and_rows():
    test_markdown = r"""# Title

| Col A | Col B |
| ----- | ----- |
| 1     | 2     |
| 3     | 4     |
"""

    doc = Document.from_text(test_markdown)

    assert len(doc.tables) == 1
    table: Table = doc.tables[0]

    assert table.header == ["Col A", "Col B"]
    assert table.rows == [
        ["1", "2"],
        ["3", "4"],
    ]
    assert table.start_line < table.end_line

    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title")
    ]


def test_links_skip_fenced_code_and_mark_global_defs():
    test_markdown = r"""# Title

Inline link to https://example.com should be captured.
As should the global link definition to [Example 2].

```bash
# This should not be treated as a header
# or the following as a link!
curl https://ignored.example.org
```

[Example 2]: https://example2.org
"""

    doc = Document.from_text(test_markdown)

    urls = {link.url: link for link in doc.links}
    assert "https://ignored.example.org" not in urls

    assert "https://example.com" in urls
    inline = urls["https://example.com"]
    assert inline.is_global is False

    assert "https://example2.org" in urls
    global_def = urls["https://example2.org"]
    assert global_def.is_global is True

    fenced = doc.fenced_lines
    assert len(fenced) == 5
    assert fenced == {6, 7, 8, 9, 10}

    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title")
    ]


def test_headings_ignore_fenced_code_blocks():
    test_markdown = r"""# Real Title

```markdown
# Fake Title
## Fake Section
```

## Real Section
"""

    doc = Document.from_text(test_markdown)

    titles = [(h.level, h.title) for h in doc.headings]
    assert (1, "Fake Title") not in titles
    assert (1, "Real Title") in titles
    assert (2, "Fake Section") not in titles
    assert (2, "Real Section") in titles


def test_tables_ignore_fenced_code_blocks():
    test_markdown = r"""# Title

```markdown
| Col A | Col B |
| ----- | ----- |
| x     | y     |
```

| Col A | Col B |
| ----- | ----- |
| 1     | 2     |
"""

    doc = Document.from_text(test_markdown)

    assert len(doc.tables) == 1
    table = doc.tables[0]
    assert table.header == ["Col A", "Col B"]
    assert table.rows == [["1", "2"]]

    sections = [(h.level, h.title) for h in doc.headings]
    assert sections == [
        (1, "Title")
    ]


def test_nested_fences_are_handled():
    test_markdown = r"""# Title

````markdown
# Markdown Block

```python
# Python Block
print("nested")
```
````

## Real Section
"""

    doc = Document.from_text(test_markdown)

    fenced = doc.fenced_lines
    assert len(fenced) == 8
    assert fenced == {3, 4, 5, 6, 7, 8, 9, 10}

    titles = [h.title for h in doc.headings]
    assert "Markdown Block" not in titles
    assert "Python Block" not in titles
    assert "Real Section" in titles
    assert "Title" in titles


def test_multiple_code_blocks():
    test_markdown = r"""# Title

```python
# Fake heading 1
```

## Real Section

```bash
# Fake heading 2
curl https://fake.example.com
```

[link]: https://real.example.com
"""

    doc = Document.from_text(test_markdown)

    fenced = doc.fenced_lines
    assert len(fenced) == 7
    assert fenced == {3, 4, 5, 9, 10, 11, 12}

    titles = [h.title for h in doc.headings]
    assert "Fake heading 1" not in titles
    assert "Fake heading 2" not in titles
    assert "Real Section" in titles
    assert "Title" in titles

    urls = [link.url for link in doc.links]
    assert "https://real.example.com" in urls
    assert "https://fake.example.com" not in urls


def test_empty_code_blocks():
    test_markdown = r"""# Title

```
```

## Section
    """

    doc = Document.from_text(test_markdown)

    fenced = doc.fenced_lines
    assert len(fenced) == 2
    assert fenced == {3, 4}

    titles = [h.title for h in doc.headings]
    assert "Title" in titles
    assert "Section" in titles


def test_table_good():
    test_markdown = r"""# Table Test

Here comes my table!

| Name    | Description |
| ------- | ----------- |
| Row 1   | The first   |
| Row 2   | The second  |
| Row 3   | The third   |
| Row 4   | The fourth  |

And another table!

| Command | Description |
| ------- | ----------- |
| `ls`    | List files  |
| `cd`    | Change dir  |
"""

    doc = Document.from_text(test_markdown)

    titles = [h.title for h in doc.headings]
    assert "Table Test" in titles

    assert len(doc.tables) == 2
    table1 = doc.tables[0]
    assert table1.header == ["Name", "Description"]
    assert len(table1.rows) == 4

    rows = [(r[0], r[1]) for r in table1.rows]
    assert rows == [
        ("Row 1", "The first"),
        ("Row 2", "The second"),
        ("Row 3", "The third"),
        ("Row 4", "The fourth"),
    ]

    table2 = doc.tables[1]
    assert table2.header == ["Command", "Description"]
    assert len(table2.rows) == 2

    rows = [(r[0], r[1]) for r in table2.rows]
    assert rows == [
        ("`ls`", "List files"),
        ("`cd`", "Change dir"),
    ]


def test_table_with_code_fence_in_cell():
    test_markdown = r"""# Title

Here comes my table!

| Command | Description |
| ------- | ----------- |
| `ls`    | List files  |
| `cd`    | Change dir  |
| `echo "$dir" \| ls`    | View contents of `$dir`  |
"""

    doc = Document.from_text(test_markdown)

    titles = [h.title for h in doc.headings]
    assert "Title" in titles

    assert len(doc.tables) == 1
    table = doc.tables[0]
    assert table.header == ["Command", "Description"]
    assert len(table.rows) == 3

    rows = [(r[0], r[1]) for r in table.rows]
    assert rows == [
        ("`ls`", "List files"),
        ("`cd`", "Change dir"),
        ("`echo \"$dir\" \\| ls`", "View contents of `$dir`"),
    ]


def test_link_in_heading():
    test_markdown = r"""
    # Title with https://example.com link

    Text with https://another.example.com
    """

    doc = Document.from_text(test_markdown)

    urls = [link.url for link in doc.links]
    assert "https://example.com" in urls
    assert "https://another.example.com" in urls


def test_special_chars_in_table_cells():
    test_markdown = r"""# Title

Here comes my table!

| Name | Value |
| ---- | ----- |
| a\rb | c     |
| d    | e\rf  |
"""

    doc = Document.from_text(test_markdown)

    titles = [h.title for h in doc.headings]
    assert "Title" in titles

    assert len(doc.tables) == 1
    table = doc.tables[0]
    assert table.header == ["Name", "Value"]
    assert len(table.rows) == 2

    rows = [(r[0], r[1]) for r in table.rows]
    assert rows == [
        (r"a\rb", "c"),
        ("d", r"e\rf")
    ]


def test_tables_too_small():
    test_markdown = r"""# Title

Here comes my (not a) table!

| Name | Value |
"""

    doc = Document.from_text(test_markdown)

    titles = [h.title for h in doc.headings]
    assert "Title" in titles

    assert len(doc.tables) == 0


def test_tables_no_divider_row():
    test_markdown = r"""# Title

Here comes my (not a) table!

| Name    | Description |
| Row 1   | The first   |
| Row 2   | The second  |
| Row 3   | The third   |
| Row 4   | The fourth  |
"""

    doc = Document.from_text(test_markdown)

    titles = [h.title for h in doc.headings]
    assert "Title" in titles

    assert len(doc.tables) == 0


def test_load_from_path():
    md = """# Title

Some content.
"""

    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as tmp:
        tmp.write(md)
        tmp_path = Path(tmp.name)

    # Now load using Document.from_path
    doc = Document.from_path(tmp_path)

    titles = [h.title for h in doc.headings]
    assert "Title" in titles
    assert "Some content." in doc.body

    tmp_path.unlink()