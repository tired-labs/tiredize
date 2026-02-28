# Standard library
from __future__ import annotations

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
