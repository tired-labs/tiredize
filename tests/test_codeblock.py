from tiredize.markdown.types.code import CodeBlock
from tiredize.types import Position

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


def test_no_codeblock():
    md_test = md_section
    matches = CodeBlock.extract(md_test)
    assert len(matches) == 0


def test_single_codeblock_normal():
    code_01 = r'''
_RE_CODEBLOCK = r"""
(?<![^|\n])
(?P<delimiter>``[`]+)
(?P<language>.*)
(?P<code>[\s\S]*?)
\1
"""
    '''.strip()
    language_01 = "python"
    delim_len_01 = 3
    delim = "`" * delim_len_01
    string_01 = f"{delim}{language_01}\n{code_01}\n{delim}"
    len_01 = len(string_01)
    position_01 = Position(line=25, offset=0, length=len_01)
    md_text = md_section.format("", string_01, "", "", "")

    matches = CodeBlock.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == CodeBlock(
        code=code_01,
        delimiter=delim,
        language=language_01,
        position=position_01,
        string=string_01
    )


def test_five_codeinlines_repeated():
    code_01 = r'''
_RE_CODEBLOCK = r"""
(?<![^|\n])
(?P<delimiter>``[`]+)
(?P<language>.*)
(?P<code>[\s\S]*?)
\1
"""
    '''.strip()
    language_01 = "python"
    delim_len_01 = 3
    delim = "`" * delim_len_01
    string_01 = f"{delim}{language_01}\n{code_01}\n{delim}"
    len_01 = len(string_01)
    positions = [
        Position(line=15, offset=0, length=len_01),
        Position(line=33, offset=0, length=len_01),
        Position(line=52, offset=0, length=len_01),
        Position(line=71, offset=0, length=len_01),
        Position(line=90, offset=0, length=len_01)
    ]

    md_text = md_section.format(
        string_01,
        string_01,
        string_01,
        string_01,
        string_01
    )

    matches = CodeBlock.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == CodeBlock(
            code=code_01,
            delimiter=delim,
            language=language_01,
            position=positions[i],
            string=string_01
        )
