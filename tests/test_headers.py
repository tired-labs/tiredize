from tiredize.markdown.types.header import Header
from tiredize.types import Position

md_section = """{}

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

Line 14, Offset 00 {}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu
malesuada eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et
enim pretium rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat.
Mauris vehicula condimentum consequat. Phasellus fermentum rhoncus enim nec
volutpat.

Line 23, Offset 00 {}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et
egestas leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec
maximus ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor.
Vivamus dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at
volutpat nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum.
Nulla vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci,
a fringilla ex. In hac habitasse platea dictumst.

Line 33, Offset 00 {}

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id
arcu porta tempus.

Line 43, Offset 00 {}

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien
eu tortor.

Line 53, Offset 00
{}"""


def test_no_headers():
    md_test = md_section
    matches = Header.extract(md_test)
    assert len(matches) == 0


def test_single_header_level01():
    level_01 = 1
    text_01 = "Header Test: Level One"
    header_01 = f"{"#" * level_01} {text_01}"
    len_01 = len(header_01)
    md_text = md_section.format(header_01, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_01),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_01,
        position=positions[0],
        title=text_01
    )


def test_single_header_level02():
    level_02 = 2
    text_02 = "Header Test: Level Two"
    header_02 = f"{"#" * level_02} {text_02}"
    len_02 = len(header_02)
    md_text = md_section.format(header_02, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_02),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_02,
        position=positions[0],
        title=text_02
    )


def test_single_header_level03():
    level_03 = 3
    text_03 = "Header Test: Level Three"
    header_03 = f"{"#" * level_03} {text_03}"
    len_03 = len(header_03)
    md_text = md_section.format(header_03, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_03),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_03,
        position=positions[0],
        title=text_03
    )


def test_single_header_level04():
    level_04 = 4
    text_04 = "Header Test: Level Four"
    header_04 = f"{"#" * level_04} {text_04}"
    len_04 = len(header_04)
    md_text = md_section.format(header_04, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_04),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_04,
        position=positions[0],
        title=text_04
    )


def test_single_header_level05():
    level_05 = 5
    text_05 = "Header Test: Level Five"
    header_05 = f"{"#" * level_05} {text_05}"
    len_05 = len(header_05)
    md_text = md_section.format(header_05, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_05),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_05,
        position=positions[0],
        title=text_05
    )


def test_single_header_level06():
    level_06 = 6
    text_06 = "Header Test: Level Six"
    header_06 = f"{"#" * level_06} {text_06}"
    len_06 = len(header_06)
    md_text = md_section.format(header_06, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_06),
    ]

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_06,
        position=positions[0],
        title=text_06
    )


def test_six_headers_repeated():
    level_01 = 1
    text_01 = "Header Test: Duplicate Headers"
    header_01 = f"{"#" * level_01} {text_01}"
    len_01 = len(header_01)
    md_text = md_section.format(header_01, "", "", "", "", "")
    positions = [
        Position(line=1, offset=0, length=len_01),
    ]

    md_text = md_section.format(
        header_01,
        header_01,
        header_01,
        header_01,
        header_01,
        header_01
    )

    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=level_01,
        position=positions[0],
        title=text_01
    )
