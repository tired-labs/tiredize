from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeInline

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


def test_no_codeinline():
    md_test = md_section
    matches = CodeInline.extract(md_test)
    assert len(matches) == 0


def test_single_codeinline_normal():
    actual_code = 'tiredize --help'
    actual_string = f"`{actual_code}`"
    actual_line = f"You can run {actual_string} to see available options."

    exp_code = actual_code
    exp_string = actual_string
    exp_position = Position(offset=1781, length=len(exp_string))

    md_text = md_section.format("", "", actual_line, "", "")

    matches = CodeInline.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == CodeInline(
        code=exp_code,
        position=exp_position,
        string=exp_string
    )


def test_five_codeinlines_repeated():
    actual_code = 'tiredize --help'
    actual_string = f"`{actual_code}`"
    actual_line = f"You can run {actual_string} to see available options."

    exp_code = actual_code
    exp_string = actual_string

    md_text = md_section.format(
        actual_line,
        actual_line,
        actual_line,
        actual_line,
        actual_line
    )

    positions = [
        Position(offset=837, length=len(exp_string)),
        Position(offset=1302, length=len(exp_string)),
        Position(offset=1891, length=len(exp_string)),
        Position(offset=2451, length=len(exp_string)),
        Position(offset=3003, length=len(exp_string))
    ]

    matches = CodeInline.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == CodeInline(
            code=exp_code,
            position=positions[i],
            string=exp_string
        )
