# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.table import Table

md_section = """# Markdown Test Section - Lorem Ipsum

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

Line 15, Offset 00
{}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu
malesuada eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et
enim pretium rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat.
Mauris vehicula condimentum consequat. Phasellus fermentum rhoncus enim nec
volutpat.

Line 25, Offset 00
{}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et
egestas leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec
maximus ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor.
Vivamus dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at
volutpat nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum.
Nulla vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci,
a fringilla ex. In hac habitasse platea dictumst.

Line 36, Offset 00
{}

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id
arcu porta tempus.

Line 47, Offset 00
{}

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien
eu tortor.

Line 58, Offset 00
{}"""


def test_no_tables():
    md_test = md_section
    regex_matches = Table.extract(md_test)
    assert len(regex_matches) == 0


def test_single_table_normal():
    actual_rows: list[str] = [
        "| Col 01  | Col 02  | Col 03  |",
        "|---------|---------|---------|",
        "| Data 01 | Data 02 | Data 03 |",
        "| Data 11 | Data 12 | Data 13 |",
        "| Data 21 | Data 22 | Data 23 |",
        "| Data 31 | Data 32 | Data 33 |",
        "| Data 41 | Data 42 | Data 43 |",
        "| Data 51 | Data 52 | Data 53 |",
    ]

    exp_divider: list[str] = [
        "---------", "---------", "---------"
    ]

    exp_header: list[str] = [
        "Col 01", "Col 02", "Col 03"
    ]

    exp_rows: list[list[str]] = [
        ["Data 01", "Data 02", "Data 03"],
        ["Data 11", "Data 12", "Data 13"],
        ["Data 21", "Data 22", "Data 23"],
        ["Data 31", "Data 32", "Data 33"],
        ["Data 41", "Data 42", "Data 43"],
        ["Data 51", "Data 52", "Data 53"]
    ]

    exp_string = '\n'.join(actual_rows) + '\n'
    exp_string_len = len(exp_string)
    md = md_section.format(exp_string, "", "", "", "")
    position = Position(offset=825, length=exp_string_len)

    regex_matches = Table.extract(md)
    assert len(regex_matches) == 1
    assert regex_matches[0] == Table(
        header=exp_header,
        divider=exp_divider,
        rows=exp_rows,
        position=position,
        string=exp_string
    )


def test_five_tables_repeated():
    actual_rows: list[str] = [
        "| Col 01  | Col 02  | Col 03  |",
        "|---------|---------|---------|",
        "| Data 01 | Data 02 | Data 03 |",
        "| Data 11 | Data 12 | Data 13 |",
        "| Data 21 | Data 22 | Data 23 |",
        "| Data 31 | Data 32 | Data 33 |",
        "| Data 41 | Data 42 | Data 43 |",
        "| Data 51 | Data 52 | Data 53 |",
    ]

    exp_divider: list[str] = [
        "---------", "---------", "---------"
    ]

    exp_header: list[str] = [
        "Col 01", "Col 02", "Col 03"
    ]

    exp_rows: list[list[str]] = [
        ["Data 01", "Data 02", "Data 03"],
        ["Data 11", "Data 12", "Data 13"],
        ["Data 21", "Data 22", "Data 23"],
        ["Data 31", "Data 32", "Data 33"],
        ["Data 41", "Data 42", "Data 43"],
        ["Data 51", "Data 52", "Data 53"]
    ]

    exp_string = '\n'.join(actual_rows) + '\n'
    exp_string_len = len(exp_string)
    md = md_section.format(
        exp_string,
        exp_string,
        exp_string,
        exp_string,
        exp_string
    )

    positions = [
        Position(offset=825, length=exp_string_len),
        Position(offset=1491, length=exp_string_len),
        Position(offset=2281, length=exp_string_len),
        Position(offset=3042, length=exp_string_len),
        Position(offset=3795, length=exp_string_len)
    ]

    regex_matches = Table.extract(md)
    assert len(regex_matches) == 5
    for i, match in enumerate(regex_matches):
        assert match == Table(
            header=exp_header,
            divider=exp_divider,
            rows=exp_rows,
            position=positions[i],
            string=exp_string
        )


# --- Regression: backtracking and code block content ---


def test_long_dashes_no_backtracking():
    """Long dash sequences without pipes must not cause backtracking."""
    text = (
        "Some heading context\n"
        " " + "-" * 50 + "\n"
        "More text after the dashes.\n"
    )
    results = Table.extract(text)
    assert len(results) == 0


def test_dashes_inside_code_block_text():
    """Table regex must not match table-like content inside code fences."""
    text = (
        "# Results\n\n"
        "```text\n"
        " SignerCertificate Status Path\n"
        " ----------------- ------ ----\n"
        " D8FB0CC66A08061B Valid mshta.exe\n"
        "```\n"
    )
    results = Table.extract(text)
    assert len(results) == 0


def test_aligned_divider():
    """Colon-aligned dividers should still be recognized as tables."""
    text = (
        "| Left | Center | Right |\n"
        "|:-----|:------:|------:|\n"
        "| a    | b      | c     |\n"
    )
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].divider == [":-----", ":------:", "------:"]


# --- Original tests ---


def test_vomit_table():
    actual_rows: list[str] = [
        "| A | B",
        "-- | -",
        "| a | b |",
        "| a | b",
        "a | b |",
        "a | b",
        "|| b        "
    ]

    exp_divider: list[str] = [
        "--", "-"
    ]

    exp_header: list[str] = [
        "A", "B"
    ]

    exp_rows: list[list[str]] = [
        ["a", "b"],
        ["a", "b"],
        ["a", "b"],
        ["a", "b"],
        ["", "b"]
    ]

    exp_string = '\n'.join(actual_rows) + '\n'
    exp_string_len = len(exp_string)
    md = md_section.format(exp_string, "", "", "", "")
    position = Position(offset=825, length=exp_string_len)

    regex_matches = Table.extract(md)
    assert len(regex_matches) == 1
    assert regex_matches[0] == Table(
        header=exp_header,
        divider=exp_divider,
        rows=exp_rows,
        position=position,
        string=exp_string
    )


# ===================================================================
#  Sanitize method (line 96)
# ===================================================================


def test_table_sanitize_preserves_length():
    text = "Before\n| A | B |\n|---|---|\n| 1 | 2 |\nAfter"
    sanitized = Table.sanitize(text)
    assert len(sanitized) == len(text)


def test_table_sanitize_no_tables():
    text = "Just text, no tables."
    sanitized = Table.sanitize(text)
    assert sanitized == text


def test_table_sanitize_idempotent():
    """Sanitize called twice produces the same result as a single call."""
    text = "| Col |\n|-----|\n| val |\n"
    first = Table.sanitize(text)
    second = Table.sanitize(first)
    assert first == second


# ===================================================================
#  Additional edge cases
# ===================================================================


def test_table_single_column():
    text = "| Col |\n|-----|\n| val |\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == ["Col"]


def test_table_base_offset():
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    results = Table.extract(text, base_offset=100)
    assert len(results) == 1
    assert results[0].position.offset == 100


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_table_extract_empty_string():
    assert Table.extract("") == []


def test_table_extract_single_char():
    assert Table.extract("|") == []


# ===================================================================
#  State mutation
# ===================================================================


def test_table_extract_does_not_mutate_input():
    text = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    original = text
    Table.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_table_unicode_cells():
    text = "| Café | Résumé |\n|------|--------|\n| ☕ | 📄 |\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == ["Café", "Résumé"]


# ===================================================================
#  Syntax variant tests (GFM spec compliance)
# ===================================================================


def test_table_over_greedy_row_matching():
    """Table rows pattern stops at lines without pipe characters."""
    text = (
        "| A |\n"
        "|---|\n"
        "| 1 |\n"
        "This is not a table row.\n"
    )
    results = Table.extract(text)
    assert len(results) == 1
    assert len(results[0].rows) == 1
    assert results[0].rows[0] == ["1"]


@pytest.mark.skip(
    reason="gfm-parity: escaped pipes in cells not handled"
)
def test_table_escaped_pipes():
    r"""GFM supports \| to include literal pipes in cells."""
    text = r"| A \| B | C |" + "\n|---|---|\n| 1 | 2 |\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == [r"A \| B", "C"]


def test_table_header_only_no_data_rows():
    """Table with only header and divider, no data rows.
    The rows group may match empty string."""
    text = "| A | B |\n|---|---|\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == ["A", "B"]


def test_table_pipe_only_data_row():
    """A data row containing only | should not crash extraction.
    Per GFM, this is a valid row with empty cells."""
    text = "| A |\n|---|\n|\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].rows == [[""]]


# ===================================================================
#  Internal CodeBlock sanitization
# ===================================================================


def test_extract_ignores_table_inside_code_fence():
    """Table.extract() should sanitize code blocks internally,
    preventing false matches on table syntax inside fences."""
    text = (
        "Some text before.\n\n"
        "```\n"
        "| Weapon | Damage |\n"
        "|--------|--------|\n"
        "| Sword  | 10     |\n"
        "```\n\n"
        "Some text after.\n"
    )
    results = Table.extract(text)
    assert len(results) == 0


def test_extract_finds_table_outside_code_fence():
    """A real table outside a code fence should still be found,
    even when a code fence with table-like content is present."""
    text = (
        "```\n"
        "| Fake | Table |\n"
        "|------|-------|\n"
        "| no   | match |\n"
        "```\n\n"
        "| Real | Table |\n"
        "|------|-------|\n"
        "| yes  | match |\n"
    )
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == ["Real", "Table"]
    assert results[0].rows == [["yes", "match"]]


def test_extract_preserves_position_after_sanitization():
    """Positions must reflect the original text, not the sanitized text.
    CodeBlock sanitization replaces content with spaces but preserves
    offsets, so table positions should be correct."""
    code_fence = (
        "```\n"
        "| Ghost | Table |\n"
        "|-------|-------|\n"
        "| boo   | 👻    |\n"
        "```\n"
    )
    real_table = (
        "| Hero | Quest |\n"
        "|------|-------|\n"
        "| Link | Zelda |\n"
    )
    text = code_fence + "\n" + real_table
    results = Table.extract(text)
    assert len(results) == 1
    expected_offset = len(code_fence) + 1  # +1 for the blank line
    assert results[0].position.offset == expected_offset


# ===================================================================
#  Cross-cutting: CRLF line endings
# ===================================================================


def test_extract_no_crash_on_sanitized_code_fence_before_divider():
    """Code fence delimiter sanitized to spaces must not match as a
    table header.  The whitespace line satisfies the old header pattern
    [^\\n|]+ but contains no pipe — it is not a valid table header.
    Regression test for table-header-empty-indexerror."""
    text = "```\nsome code\n```\n|---|\n|1|\n"
    results = Table.extract(text)
    # The code fence is sanitized, leaving whitespace where ``` was.
    # The whitespace line + |---| must NOT be parsed as a table.
    assert len(results) == 0


def test_extract_no_crash_on_whitespace_only_pipe_header():
    """A header line containing only a pipe and whitespace (e.g., ' | ')
    must not crash.  After stripping outer pipes the header is empty,
    so the match should be skipped.
    Regression test for table-header-empty-indexerror."""
    text = " | \n|---|\n|1|\n"
    results = Table.extract(text)
    assert len(results) == 0


@pytest.mark.skip(
    reason="gfm-parity: CRLF line endings not supported in tables"
)
def test_table_crlf():
    """Tables with CRLF line endings should match."""
    text = "| A |\r\n|---|\r\n| 1 |\r\n"
    results = Table.extract(text)
    assert len(results) == 1
    assert results[0].header == ["A"]
