from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass
class InlineImage:
    text: str
    position: Position
    string: str
    title: typing.Optional[str]
    url: str

    _RE_INLINE_IMAGE = r"""
        !\[                           # Opening (exclamation mark and bracket)
        \s*                           # Optional whitespace
        (?P<text>[^]]*?)              # Capture the title
        \s*                           # Optional whitespace
        \]\(                          # Closing bracket, opening parenthesis
        \s*                           # Optional whitespace
        (?P<url>\S+)                  # Capture the URL
        (\s*?\"(?P<title>[^"]*?)\")?  # Capture optional title
        \s*\)                         # Closing parenthesis
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
                    position=Position(
                        line=line_num,
                        offset=offset,
                        length=length
                    ),
                    string=match.group(),
                    text=match.group("text"),
                    title=match.group("title"),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any inline images with whitespace
        """
        return sanitize_text(InlineImage._RE_INLINE_IMAGE, text)
