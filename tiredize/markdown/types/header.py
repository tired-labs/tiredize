from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.markdown.types.code import CodeBlock
from tiredize.types import Position
import typing


@dataclass
class Header:
    level: int
    position: Position
    string: str
    title: str

    _RE_HEADER = r"""
        (?<![^|\n])           # Start of line, but don't capture it
        (?P<hashes>\#{1,6})   # One to six hash characters
        \s+                   # Whitespace
        (?P<title>[^\n]+)     # Capture anything after that as the title
    """

    @staticmethod
    def extract(text: str) -> typing.List["Header"]:
        """
        Extract markdown titles from a section.
        As we are expecting a section's text to be the input, this must be the
        first thing appearing in the text provided.
        """
        matches = search_all_re(
            Header._RE_HEADER,
            CodeBlock.sanitize(text)
        )

        result: list[Header] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            level = len(match.group("hashes"))

            result.append(
                Header(
                    level=level,
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group(),
                    title=match.group("title")
                )
            )
        return result
