from tiredize.core_types import Position
from tiredize.markdown.types.header import Header

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


def test_no_headers():
    md_test = md_section
    matches = Header.extract(md_test)
    assert len(matches) == 0


def test_single_header_level01():
    actual_level = 1
    actual_text = "Header Test: Level One"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-one"
    exp_string = "# Header Test: Level One"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level02():
    actual_level = 2
    actual_text = "Header Test: Level Two"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-two"
    exp_string = "## Header Test: Level Two"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level03():
    actual_level = 3
    actual_text = "Header Test: Level Three"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-three"
    exp_string = "### Header Test: Level Three"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level04():
    actual_level = 4
    actual_text = "Header Test: Level Four"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-four"
    exp_string = "#### Header Test: Level Four"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level05():
    actual_level = 5
    actual_text = "Header Test: Level Five"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-five"
    exp_string = "##### Header Test: Level Five"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_single_header_level06():
    actual_level = 6
    actual_text = "Header Test: Level Six"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_slug = "#header-test-level-six"
    exp_string = "###### Header Test: Level Six"
    exp_position = Position(offset=0, length=len(actual_string))

    md_text = md_section.format(actual_string, "", "", "", "", "")
    matches = Header.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == Header(
        level=actual_level,
        position=exp_position,
        slug=exp_slug,
        string=exp_string,
        title=actual_text
    )


def test_six_headers_repeated():
    actual_level = 1
    actual_text = "Header Test: Duplicate Level One"
    actual_string = f"{'#' * actual_level} {actual_text}"

    exp_string = "# Header Test: Duplicate Level One"
    exp_slugs = [
        "#header-test-duplicate-level-one",
        "#header-test-duplicate-level-one-1",
        "#header-test-duplicate-level-one-2",
        "#header-test-duplicate-level-one-3",
        "#header-test-duplicate-level-one-4",
        "#header-test-duplicate-level-one-5",
    ]
    exp_positions = [
        Position(offset=0, length=len(actual_string)),
        Position(offset=822, length=len(actual_string)),
        Position(offset=1266, length=len(actual_string)),
        Position(offset=1834, length=len(actual_string)),
        Position(offset=2373, length=len(actual_string)),
        Position(offset=2904, length=len(actual_string))
    ]

    md_text = md_section.format(
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string
    )
    matches = Header.extract(md_text)
    assert len(matches) == 6
    for i, match in enumerate(matches):
        assert match == Header(
            level=actual_level,
            position=exp_positions[i],
            slug=exp_slugs[i],
            string=exp_string,
            title=actual_text
        )
