from tiredize.markdown.types.image import InlineImage
from tiredize.types import Position

md_section = """# Markdown Test Section - Lorem Ipsum

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean dapibus auctor
mattis. Donec eu posuere ex. Morbi faucibus, diam vitae interdum viverra, diam
nulla tempor tellus, non maximus nulla elit eget arcu. Nam quam turpis, finibus
non velit vel, pellentesque mattis magna. Nunc tempus ultricies pharetra. Mauris
rutrum vel purus eu facilisis. Proin laoreet facilisis libero ac ultricies.
Quisque lectus tellus, maximus nec tellus ut, vestibulum faucibus nulla.
Pellentesque vel ante egestas, aliquet neque a, egestas mauris. Quisque
vulputate metus imperdiet, rhoncus odio eu, dapibus justo. Fusce porta magna in
efficitur tincidunt. Vestibulum efficitur ex porttitor neque suscipit pulvinar.
Nulla mauris libero, semper in ultricies eu, interdum eget justo.

Line 14, Offset 19 {}

Donec quis erat non diam sollicitudin faucibus quis quis arcu. In posuere vel
dolor vitae aliquet. Maecenas ultrices dignissim orci, id aliquet arcu malesuada
eu. Quisque congue ex ac dictum faucibus. Curabitur mollis leo et enim pretium
rhoncus. Etiam at lorem vel diam viverra malesuada vel ut erat. Mauris vehicula
condimentum consequat. Phasellus fermentum rhoncus enim nec volutpat.

Line 23
Offset 10 {}

Nulla facilisi. Vestibulum ut turpis ut ipsum euismod varius. Integer et egestas
leo. Etiam et porttitor turpis, et dignissim diam. Suspendisse nec maximus
ipsum, eget convallis lorem. Donec consequat blandit nisi at porttitor. Vivamus
dictum ante a odio varius fringilla. Donec scelerisque nisi dolor, at volutpat
nibh aliquam in. Maecenas vestibulum nulla a efficitur vestibulum. Nulla
vulputate pulvinar diam, non sollicitudin leo. Suspendisse id porta orci, a
fringilla ex. In hac habitasse platea dictumst.

Line 33 with an offset of 29 {} and surrounding text.

Cras venenatis semper justo, eget feugiat turpis mollis non. Suspendisse risus
lacus, pulvinar ut ipsum nec, pharetra blandit leo. Vivamus ullamcorper magna
sit amet dolor dapibus porta. Pellentesque habitant morbi tristique senectus et
netus et malesuada fames ac turpis egestas. Aenean eget mollis nulla. Donec
risus ex, malesuada fermentum sem in, molestie viverra sem. Ut odio massa,
luctus egestas maximus non, venenatis id justo. Suspendisse eleifend est id arcu
porta tempus.

L43, O09 {} with surrounding text.

Curabitur id nulla sit amet felis porta tempus. Morbi placerat malesuada dolor,
pulvinar tempor enim laoreet eget. Nullam consequat, magna ac dapibus bibendum,
magna enim aliquet turpis, vitae facilisis sapien velit sed odio. Duis eu
condimentum lorem. Maecenas quam magna, condimentum ac ultrices sit amet,
pellentesque et metus. Donec placerat et sem ut auctor. Suspendisse molestie,
quam ac pretium varius, libero enim placerat dolor, eget sagittis urna sapien eu
tortor.

L53, Offset 15 {}"""

def test_no_images():
    md_test = md_section
    matches = InlineImage.extract(md_test)
    assert len(matches) == 0


def test_single_image_normal():
    alttext_01 = "Alt Text"
    url_01 = "https://example.com/image1.png"
    title_01 = "Image Title 1"
    image_01 = f"![{alttext_01}]({url_01} \"{title_01}\")"
    position_01 = Position(line=14, offset=19, length=59)
    md_text = md_section.format(image_01, "", "", "", "")

    matches = InlineImage.extract(md_text)
    assert len(matches) == 1
    assert matches[0] == InlineImage(
        alt_text=alttext_01,
        string=image_01,
        position=position_01,
        title_text=title_01,
        url=url_01
    )


def test_five_images_repeated():
    alttext_01 = "Alt Text"
    url_01 = "https://example.com/image1.png"
    title_01 = "Image Title 1"
    image_01 = f"![{alttext_01}]({url_01} \"{title_01}\")"
    len_01 = len(image_01)
    positions = [
        Position(line=14, offset=19, length=len_01),
        Position(line=23, offset=10, length=len_01),
        Position(line=33, offset=29, length=len_01),
        Position(line=43, offset=9, length=len_01),
        Position(line=53, offset=15, length=len_01)
    ]

    md_text = md_section.format(
        image_01,
        image_01,
        image_01,
        image_01,
        image_01
    )

    matches = InlineImage.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == InlineImage(
            alt_text=alttext_01,
            string=image_01,
            position=positions[i],
            title_text=title_01,
            url=url_01
        )


def test_five_images_unique():
    alttext_01 = "Image 01 Alt Text"
    url_01 = "https://firstimage.com/image01.png"
    title_01 = "Image 01 Title"
    image_01 = f"![{alttext_01}]({url_01} \"{title_01}\")"
    position_01 = Position(line=14, offset=19, length=len(image_01))

    alttext_02 = "Second Alt Text"
    url_02 = "https://secondvisual.com/2.jpg"
    title_02 = "Title 2"
    image_02 = f"![{alttext_02}]({url_02} \"{title_02}\")"
    position_02 = Position(line=23, offset=10, length=len(image_02))

    alttext_03 = "No Title for the 3rd Image"
    url_03 = "https://3.com/3.png"
    image_03 = f"![{alttext_03}]({url_03})"
    position_03 = Position(line=33, offset=29, length=len(image_03))

    alttext_04 = "Local Image for the Fourth Test"
    url_04 = "./images/img4.svg"
    title_04 = "4th"
    image_04 = f"![{alttext_04}]({url_04} \"{title_04}\")"
    position_04 = Position(line=43, offset=9, length=len(image_04))

    alttext_05 = "Fifth Image With Alt Text"
    url_05 = "https://example.com/image1.png"
    image_05 = f"![{alttext_05}]({url_05})"
    position_05 = Position(line=53, offset=15, length=len(image_05))

    expected = [
        InlineImage(
            alt_text=alttext_01,
            string=image_01,
            position=position_01,
            title_text=title_01,
            url=url_01
        ), InlineImage(
            alt_text=alttext_02,
            string=image_02,
            position=position_02,
            title_text=title_02,
            url=url_02
        ), InlineImage(
            alt_text=alttext_03,
            string=image_03,
            position=position_03,
            title_text="",
            url=url_03
        ), InlineImage(
            alt_text=alttext_04,
            string=image_04,
            position=position_04,
            title_text=title_04,
            url=url_04
        ), InlineImage(
            alt_text=alttext_05,
            string=image_05,
            position=position_05,
            title_text="",
            url=url_05
        )
    ]

    md_text = md_section.format(
        image_01,
        image_02,
        image_03,
        image_04,
        image_05
    )

    matches = InlineImage.extract(md_text)
    assert len(matches) == 5
    for i, match in enumerate(matches):
        assert match == expected[i]
