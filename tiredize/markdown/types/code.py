from dataclasses import dataclass
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass(frozen=True)
class CodeBlock:
    content: str
    position: Position
    syntax: str

    RE_CODEBLOCK = r"""
        ^                     # Must be at the start of a line
        (?P<delimiter>``[`]+) # Opening backticks (three or more)
        (?P<syntax>.*)        # Capture the syntax if present
        $                     # Line ends here
    """

    @staticmethod
    def extract(text: str) -> typing.List[CodeBlock]:
        """
        Extract markdown codeblocks from text.
        """
        codeblocks = search_all_re(
            CodeBlock.RE_CODEBLOCK,
            text
        )

        result: list[CodeBlock] = []
        for codeblock in codeblocks:
            result.append(
                CodeBlock(
                    content=codeblock["groupdict"]["code"],
                    position=Position(
                        line_start=codeblock["line_start"],
                        line_end=codeblock["line_end"],
                        char_start=codeblock["start"],
                        char_end=codeblock["end"]
                    ),
                    syntax=""
                )
            )
        return result


@dataclass(frozen=True)
class CodeInline:
    content: str
    end: int
    start: int

    RE_CODE_INLINE = r"""
        [^\S\s^]?    # Exclude any characters before the backtick
        `            # Opening backtick
        [^\n`]+      # Capture anything except backtick or newline
        `            # Closing backtick
    """
