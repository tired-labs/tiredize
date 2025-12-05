from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass(frozen=True)
class Header:
    level: int
    position: Position
    title: str

    _RE_HEADER = r"""
        ^                     # Must be at the start of a line
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
            text
        )

        result: list[Header] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            level = len(match.group("hashes"))

            result.append(
                Header(
                    level=level,
                    position=Position(
                        line=line_num,
                        offset=offset,
                        length=length
                    ),
                    title=match.group("title")
                )
            )
        return result
