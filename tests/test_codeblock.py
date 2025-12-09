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
    regex_matches = CodeBlock.extract(md_test)
    assert len(regex_matches) == 0


def test_single_codeblock_normal():
    actual_code = '_RE_CODEBLOCK = r""""\n'
    actual_code += r'(?<![^\\\\n' + '\n'
    actual_code += '])\n'
    actual_code += '(?P<delimiter>``[`]+)\n'
    actual_code += '(?P<language>.*)\n'
    actual_code += '(?P<code>[\\\\s\\\\S]*?)\n'
    actual_code += '\\1"""'

    actual_language = "python"

    actual_string = '```' + actual_language + '\n'
    actual_string += actual_code + '\n'
    actual_string += '```'

    exp_code = actual_code
    exp_delimiter = "```"
    exp_language = actual_language
    exp_string = actual_string
    exp_position = Position(line=25, offset=0, length=len(exp_string))

    md_text = md_section.format("", actual_string, "", "", "")
    regex_matches = CodeBlock.extract(md_text)

    assert len(regex_matches) == 1
    assert regex_matches[0] == CodeBlock(
        code=exp_code,
        delimiter=exp_delimiter,
        language=exp_language,
        position=exp_position,
        string=exp_string
    )


def test_five_codeblocks_repeated():
    actual_code = '_RE_CODEBLOCK = r""""\n'
    actual_code += r'(?<![^\\\\n' + '\n'
    actual_code += '])\n'
    actual_code += '(?P<delimiter>``[`]+)\n'
    actual_code += '(?P<language>.*)\n'
    actual_code += '(?P<code>[\\\\s\\\\S]*?)\n'
    actual_code += '\\1"""'

    actual_language = "python"

    actual_string = '```' + actual_language + '\n'
    actual_string += actual_code + '\n'
    actual_string += '```'

    exp_code = actual_code
    exp_delimiter = "```"
    exp_language = actual_language
    exp_string = actual_string

    md_text = md_section.format(
        actual_string,
        actual_string,
        actual_string,
        actual_string,
        actual_string
    )

    positions = [
        Position(line=15, offset=0, length=len(exp_string)),
        Position(line=33, offset=0, length=len(exp_string)),
        Position(line=52, offset=0, length=len(exp_string)),
        Position(line=71, offset=0, length=len(exp_string)),
        Position(line=90, offset=0, length=len(exp_string))
    ]

    regex_matches = CodeBlock.extract(md_text)
    assert len(regex_matches) == 5
    for i, match in enumerate(regex_matches):
        assert match == CodeBlock(
            code=exp_code,
            delimiter=exp_delimiter,
            language=exp_language,
            position=positions[i],
            string=exp_string
        )
