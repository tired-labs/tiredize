from tiredize.document import Document, Table
import pytest
import textwrap


def make_doc(md: str) -> Document:
    """Helper to build a Document from inline markdown."""
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


def test_front_matter_and_body_split():
    md = """
    ---
    title: Example
    tags:
      - one
      - two
    ---
    # Heading 1

    Body text.
    """

    doc = make_doc(md)

    assert doc.front_matter == {
        "title": "Example",
        "tags": ["one", "two"],
    }
    assert "# Heading 1" in doc.body
    assert "Body text." in doc.body


def test_headings_are_parsed_with_levels_and_lines():
    md = """
    # Title

    Some text.

    ## Section One

    More text.

    ### Subsection
    """

    doc = make_doc(md)

    titles = [(h.level, h.title) for h in doc.headings]
    assert titles == [
        (1, "Title"),
        (2, "Section One"),
        (3, "Subsection"),
    ]

    # Sanity check that line numbers are monotonic
    lines = [h.line for h in doc.headings]
    assert lines == sorted(lines)


def test_fenced_lines_track_code_blocks():
    md = """
    # Title

    ```python
    print("inside")
    ```
    Outside
    """

    doc = make_doc(md)

    # All lines of the code block including fences should be marked fenced
    fenced = doc.fenced_lines
    assert len(fenced) >= 3
    # There should be at least one non fenced line in the document
    total_lines = len(doc.body.splitlines())
    assert any(i not in fenced for i in range(1, total_lines + 1))


def test_tables_are_extracted_with_header_and_rows():
    md = """
    # Title

    | Col A | Col B |
    | ----- | ----- |
    | 1     | 2     |
    | 3     | 4     |
    """

    doc = make_doc(md)

    assert len(doc.tables) == 1
    table: Table = doc.tables[0]

    assert table.header == ["Col A", "Col B"]
    assert table.rows == [
        ["1", "2"],
        ["3", "4"],
    ]
    assert table.start_line < table.end_line


def test_links_skip_fenced_code_and_mark_global_defs():
    md = """
    # Title

    Inline link to https://example.com should be captured.

    ```bash
    # This should not be treated as a link:
    curl https://ignored.example.org
    ```

    [ref]: https://example.org
    """

    doc = make_doc(md)

    urls = {link.url: link for link in doc.links}

    assert "https://example.com" in urls
    assert "https://ignored.example.org" not in urls
    assert "https://example.org" in urls

    inline = urls["https://example.com"]
    global_def = urls["https://example.org"]

    assert inline.is_global is False
    assert global_def.is_global is True


def test_headings_ignore_fenced_code_blocks():
    md = """
    # Real Title

    ```markdown
    # Fake Title
    ## Fake Section
    ```

    ## Real Section
    """

    doc = make_doc(md)

    # Expect only the "real" headings outside the fenced code block
    titles = [(h.level, h.title) for h in doc.headings]

    assert (1, "Real Title") in titles
    assert (2, "Real Section") in titles

    # These should not appear once we fix the parser
    assert (1, "Fake Title") not in titles
    assert (2, "Fake Section") not in titles


def test_tables_ignore_fenced_code_blocks():
    md = """
    # Title

    ```markdown
    | Col A | Col B |
    | ----- | ----- |
    | x     | y     |
    ```

    | Col A | Col B |
    | ----- | ----- |
    | 1     | 2     |
    """

    doc = make_doc(md)

    # Once behavior is correct, only the table outside the code block should be
    # parsed
    assert len(doc.tables) == 1

    table = doc.tables[0]
    assert table.header == ["Col A", "Col B"]
    assert table.rows == [["1", "2"]]


def test_nested_fences_are_handled():
    """Test that code blocks with triple backticks inside are handled."""
    md = """
    # Title

    ````markdown
    ```python
    print("nested")
    ```
    ````

    ## Real Section
    """

    doc = make_doc(md)

    # Should only see headings outside the fenced block
    titles = [h.title for h in doc.headings]
    assert "Title" in titles
    assert "Real Section" in titles


def test_multiple_code_blocks():
    md = """
    # Title

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

    doc = make_doc(md)

    # Should skip both code blocks
    titles = [h.title for h in doc.headings]
    assert "Title" in titles
    assert "Real Section" in titles

    urls = [link.url for link in doc.links]
    assert "https://real.example.com" in urls
    assert "https://fake.example.com" not in urls


def test_empty_code_blocks():
    md = """
    # Title

    ```
    ```

    ## Section
    """

    doc = make_doc(md)

    fenced = doc.fenced_lines
    assert len(fenced) == 2  # Just the two fence lines

    titles = [h.title for h in doc.headings]
    assert "Title" in titles
    assert "Section" in titles


def test_table_with_code_fence_in_cell():
    """Table cells can contain inline code backticks."""
    md = """
    | Command | Description |
    | ------- | ----------- |
    | `ls`    | List files  |
    | `cd`    | Change dir  |
    """

    doc = make_doc(md)

    assert len(doc.tables) == 1
    table = doc.tables[0]
    assert table.header == ["Command", "Description"]
    assert len(table.rows) == 2


def test_link_in_heading():
    md = """
    # Title with https://example.com link

    Text with https://another.example.com
    """

    doc = make_doc(md)

    urls = [link.url for link in doc.links]
    assert "https://example.com" in urls
    assert "https://another.example.com" in urls


@pytest.mark.filterwarnings("ignore:invalid escape sequence.*SyntaxWarning")
def test_special_chars_in_table_cells():
    md = r"""
    | Name | Value |
    | ---- | ----- |
    | a\|b | c     |    # noqa: W605
    | d    | e\|f  |    # noqa: W605
    """

    doc = make_doc(md)

    # This documents current behavior with escaped pipes
    assert len(doc.tables) == 1
