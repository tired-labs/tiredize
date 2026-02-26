# Local
from tiredize.core_types import Position
from tiredize.markdown.types.quoteblock import QuoteBlock

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


def test_no_quoteblocks():
    md_test = md_section
    matches = QuoteBlock.extract(md_test)
    assert len(matches) == 0


def test_single_quoteblock_normal():
    depth_01 = 1
    text_01 = "Four score and seven years ago...."
    quote_01 = f"{'>' * depth_01} {text_01}"
    len_01 = len(quote_01)
    position_01 = Position(offset=825, length=len_01)
    md_text = md_section.format(quote_01, "", "", "", "")

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == QuoteBlock(
        depth=depth_01,
        position=position_01,
        quote=text_01,
        string=quote_01
    )


def test_single_quoteblock_multiline():
    depth_01 = 1
    quote_lines = [
        "Four score and seven years ago....",
        "Our fathers brought forth on this continent, a new nation,",
        "conceived in Liberty, and dedicated to the proposition that",
        "all men are created equal."
    ]
    quote_multiline = "> " + "\n> ".join(quote_lines).lstrip("\n")
    len_multiline = len(quote_multiline)
    position_multiline = Position(offset=825, length=len_multiline)
    md_text = md_section.format(quote_multiline, "", "", "", "")

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == QuoteBlock(
        depth=depth_01,
        position=position_multiline,
        quote="\n".join(quote_lines),
        string=quote_multiline
    )


def test_five_quoteblocks_repeated():
    depth_01 = 1
    text_01 = "Four score and seven years ago...."
    quote_01 = f"{'>' * depth_01} {text_01}"
    len_01 = len(quote_01)
    positions = [
        Position(offset=825, length=len_01),
        Position(offset=1271, length=len_01),
        Position(offset=1841, length=len_01),
        Position(offset=2382, length=len_01),
        Position(offset=2915, length=len_01)
    ]

    md_text = md_section.format(
        quote_01,
        quote_01,
        quote_01,
        quote_01,
        quote_01
    )

    matches = QuoteBlock.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == QuoteBlock(
            depth=depth_01,
            string=quote_01,
            position=positions[i],
            quote=text_01
        )
