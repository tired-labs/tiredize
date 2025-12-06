from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass
class InlineImage:
    alt_text: str
    position: Position
    string: str
    title: typing.Optional[str]
    url: str

    _RE_INLINE_IMAGE = r"""
        !\[                       # Opening (exclamation mark and bracket)
        (?P<alttext>[^]]*)        # Capture the alt-text
        \]\(                      # Closing bracket, opening paren
        (?P<url>[\s]*[^\s\)]*)    # Capture the URL
        \s*"*                     # Support for optional title
        (?P<title>.*?)            # Capture optional title text
        "*?\s*?\)                 # Closing characters
    """

    @staticmethod
    def extract(text: str) -> typing.List["InlineImage"]:
        """
        Extract markdown images from text.
        """
        matches = search_all_re(
            InlineImage._RE_INLINE_IMAGE,
            text
        )

        result: list[InlineImage] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                InlineImage(
                    alt_text=match.group("alttext"),
                    position=Position(
                        line=line_num,
                        offset=offset,
                        length=length
                    ),
                    string=match.group(),
                    title=match.group("title"),
                    url=match.group("url")
                )
            )
        return result
