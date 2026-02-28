# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock

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
    exp_position = Position(offset=1235, length=len(exp_string))

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
        Position(offset=825, length=len(exp_string)),
        Position(offset=1351, length=len(exp_string)),
        Position(offset=2001, length=len(exp_string)),
        Position(offset=2622, length=len(exp_string)),
        Position(offset=3235, length=len(exp_string))
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


# =========================================================================
#  Sanitize method
# =========================================================================


def test_codeblock_sanitize_preserves_length():
    text = "Before\n```python\nprint('hello')\n```\nAfter"
    sanitized = CodeBlock.sanitize(text)
    assert len(sanitized) == len(text)
    assert "print" not in sanitized


def test_codeblock_sanitize_no_code_blocks():
    text = "Just text, no code blocks here."
    sanitized = CodeBlock.sanitize(text)
    assert sanitized == text


def test_codeblock_sanitize_idempotent():
    text = "Before\n```python\nprint('hello')\n```\nAfter"
    first = CodeBlock.sanitize(text)
    second = CodeBlock.sanitize(first)
    assert first == second
    assert len(second) == len(text)


# =========================================================================
#  Edge cases
# =========================================================================


def test_codeblock_four_backticks():
    """Four backtick delimiter should match with four backtick closing."""
    text = "````\ncode\n````"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].delimiter == "````"


def test_codeblock_no_language():
    text = "```\nplain code\n```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].language == ""


def test_codeblock_base_offset():
    text = "```\ncode\n```"
    results = CodeBlock.extract(text, base_offset=50)
    assert len(results) == 1
    assert results[0].position.offset == 50


# =========================================================================
#  Syntax variant tests (GFM spec compliance)
# =========================================================================


@pytest.mark.skip(reason="gfm-parity: tilde-fenced code blocks not supported")
def test_codeblock_tilde_fence():
    """GFM supports ~~~ fences. Should match like backtick fences."""
    text = "~~~\ncode\n~~~"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == "code"


def test_codeblock_closing_with_extra_backticks():
    """GFM allows closing fence >= opening length. The backreference
    finds the 3-backtick substring within the 5-backtick closing,
    so this correctly matches."""
    text = "```\ncode\n`````"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == "code"


@pytest.mark.skip(reason="gfm-parity: indented code fences not supported")
def test_codeblock_indented_fence():
    """GFM allows 1-3 spaces before opening/closing fence."""
    text = "   ```\ncode\n   ```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == "code"


# ===================================================================
#  Boundary and degenerate inputs
# ===================================================================


def test_codeblock_extract_empty_string():
    assert CodeBlock.extract("") == []


def test_codeblock_extract_single_char():
    assert CodeBlock.extract("`") == []


# ===================================================================
#  State mutation
# ===================================================================


def test_codeblock_extract_does_not_mutate_input():
    text = "```\ncode\n```"
    original = text
    CodeBlock.extract(text)
    assert text == original


# ===================================================================
#  Unicode
# ===================================================================


def test_codeblock_unicode_content():
    text = "```\n日本語コード = 42\ncafé = True\n```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert "日本語コード" in results[0].code


def test_codeblock_sanitize_unicode_preserves_length():
    text = "```\nvar café = '☕'\n```"
    sanitized = CodeBlock.sanitize(text)
    assert len(sanitized) == len(text)


# ===================================================================
#  Additional syntax variant tests
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: closing fence with trailing spaces not matched"
)
def test_codeblock_closing_fence_trailing_spaces():
    """GFM allows trailing spaces after closing fence."""
    text = "```\ncode\n```   "
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == "code"


@pytest.mark.skip(
    reason="gfm-parity: empty code block not matched"
)
def test_codeblock_empty():
    """GFM allows empty code blocks with no content lines."""
    text = "```\n```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == ""


def test_codeblock_after_pipe_char():
    """The (?<![^|\\n]) anchor treats | as valid start-of-line.
    Code fence after | produces a false positive match."""
    text = "|```\ncode\n```"
    results = CodeBlock.extract(text)
    # Per GFM, | before ``` should not start a code block.
    # The anchor (?<![^|\\n]) means "preceding char must be |
    # or \\n (or start of string)", so | is accepted.
    # This is a false positive.
    assert len(results) == 1  # documents actual behavior


# ===================================================================
#  Cross-type: nested code
# ===================================================================


def test_inline_code_inside_code_block():
    """Inline code backticks inside a fenced code block should not
    produce CodeInline matches when CodeInline sanitizes CodeBlock
    first (which it doesn't -- CodeInline has no sanitization)."""
    from tiredize.markdown.types.code import CodeInline
    text = "```\n`inline` code\n```"
    results = CodeInline.extract(text)
    # CodeInline does NOT sanitize CodeBlock, so it finds `inline`
    # inside the fence. This is a false positive.
    # We document actual behavior: it matches.
    assert len(results) == 1
    assert results[0].code == "inline"


def test_code_block_fence_inside_inline_code():
    """Fenced code markers inside backticks should not produce
    CodeBlock matches. This is an edge case."""
    text = "Use ```` to start code."
    results = CodeBlock.extract(text)
    assert len(results) == 0


# ===================================================================
#  Cross-cutting: CRLF line endings
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: CRLF line endings not supported"
)
def test_codeblock_crlf():
    """Code blocks with CRLF line endings should match."""
    text = "```\r\ncode\r\n```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
    assert results[0].code == "code"


# ===================================================================
#  Cross-cutting: leading indentation
# ===================================================================


@pytest.mark.skip(
    reason="gfm-parity: indented code fences not supported"
)
def test_codeblock_one_space_indent():
    """GFM allows 1 space before opening fence."""
    text = " ```\ncode\n ```"
    results = CodeBlock.extract(text)
    assert len(results) == 1
