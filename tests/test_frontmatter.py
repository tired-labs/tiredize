from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.types import Position
import datetime
import typing
import yaml

md_section = """{}# Markdown Test Section - Lorem Ipsum

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


def test_no_frontmatter():
    md_test = md_section
    frontmatter = FrontMatter.extract(md_test)
    assert frontmatter is None


def test_single_frontmatter_normal():
    example_data: typing.Dict[str, typing.Any] = {
        'title': 'Markdown Frontmatter Example',
        'id': 4444,
        'publication_date': datetime.datetime.now(),
        'tags': ['YAML', 'Markdown', 'TIRED']
    }
    yaml_01 = yaml.safe_dump(example_data)
    frontmatter_01 = f"---\n{yaml_01}\n---\n"
    len_01 = len(frontmatter_01)
    position_01 = Position(line=1, offset=0, length=len_01)
    md_text = md_section.format(frontmatter_01, "", "", "", "", "")

    expected = FrontMatter(
        content=example_data,
        string=frontmatter_01,
        position=position_01
    )

    frontmatter = FrontMatter.extract(md_text)
    assert frontmatter is not None
    assert frontmatter == expected


def test_six_frontmatters_repeated():
    example_data: typing.Dict[str, typing.Any] = {
        'title': 'Markdown Frontmatter Example',
        'id': 4444,
        'publication_date': datetime.datetime.now(),
        'tags': ['YAML', 'Markdown', 'TIRED']
    }
    yaml_01 = yaml.safe_dump(example_data)
    frontmatter_01 = f"---\n{yaml_01}\n---\n"
    len_01 = len(frontmatter_01)
    position_01 = Position(line=1, offset=0, length=len_01)
    md_text = md_section.format(
        frontmatter_01,
        frontmatter_01,
        frontmatter_01,
        frontmatter_01,
        frontmatter_01,
        frontmatter_01
    )

    expected = FrontMatter(
        content=example_data,
        string=frontmatter_01,
        position=position_01
    )

    frontmatter = FrontMatter.extract(md_text)
    assert frontmatter is not None
    assert frontmatter == expected
