from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass
class CodeBlock:
    code: str
    delimiter: str
    language: str
    position: Position
    string: str

    _RE_CODEBLOCK = r"""
        (?<![^|\n])
        (?P<delimiter>``[`]+)
        (?P<language>.*)
        \n
        (?P<code>[\s\S]*?)
        \n
        \1
    """

    @staticmethod
    def extract(text: str) -> typing.List["CodeBlock"]:
        """
        Extract fenced codeblocks from markdown text.
        """
        matches = search_all_re(
            CodeBlock._RE_CODEBLOCK,
            text
        )

        result: list[CodeBlock] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)

            result.append(
                CodeBlock(
                    code=match.group("code"),
                    delimiter=match.group("delimiter"),
                    language=match.group("language"),
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group()
                )
            )
        return result


@dataclass
class CodeInline:
    code: str
    position: Position
    string: str

    _RE_CODE_INLINE = r"""
        `                  # Opening backtick
        (?P<code>[^\n`]+)  # Capture anything except backtick or newline
        `                  # Closing backtick
    """

    @staticmethod
    def extract(text: str) -> typing.List["CodeInline"]:
        """
        Extract inline code from markdown text.
        """
        matches = search_all_re(
            CodeInline._RE_CODE_INLINE,
            text
        )

        result: list[CodeInline] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)

            result.append(
                CodeInline(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group(),
                    code=match.group("code")
                )
            )
        return result
