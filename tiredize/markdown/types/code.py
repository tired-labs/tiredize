from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing

@dataclass(frozen=True)
class CodeBlock:
    code: str
    language: str
    position: Position
    string: str

    _RE_CODEBLOCK = r"""
        ^                     # Must be at the start of a line
        (?P<delimiter>``[`]+) # Opening backticks (three or more)
        (?P<language>.*)      # Capture the language if present
        $                     # Line ends here
    """


@dataclass(frozen=True)
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
 