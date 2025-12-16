from dataclasses import dataclass
from tiredize.core_types import Position
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
import typing


@dataclass(frozen=False)
class InlineImage:
    text: str
    position: Position
    string: str
    title: typing.Optional[str]
    url: str

    RE_INLINE_IMAGE = r"""
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
    def extract(text: str, base_offset: int = 0) -> typing.List["InlineImage"]:
        """
        Extract markdown images from text.
        """
        matches = search_all_re(
            InlineImage.RE_INLINE_IMAGE,
            text
        )

        result: list[InlineImage] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )
            result.append(
                InlineImage(
                    position=position,
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
        Replace any Inline Images with whitespace
        """
        return sanitize_text(InlineImage.RE_INLINE_IMAGE, text)
