from dataclasses import dataclass
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass(frozen=True)
class InlineImage:
    alt_text: str
    position: Position
    string: str
    title_text: typing.Optional[str]
    url: str

    _RE_IMAGE_INLINE = r"""
        !\[                              # Opening (exclamation mark and bracket)
        (?P<alttext>[^]]*)               # Capture the alt-text
        \]\(                             # Closing bracket, opening paren
        (?P<url>[\s]*[^\s\)]*)           # Capture the URL
        \s*"*                            # Support for optional title
        (?P<title>.*?)                   # Capture optional title text
        "*?\s*?\)                        # Closing characters
    """

    @staticmethod
    def extract(text: str) -> typing.List[InlineImage]:
        """
        Extract markdown images from text.
        """
        matches = search_all_re(
            InlineImage._RE_IMAGE_INLINE,
            text
        )

        result: list[InlineImage] = []
        for match in matches:
            string = match.group()
            line_num = text[:match.start()].count("\n") + 1
            offset = match.start() - text.rfind("\n", 0, match.start())
            result.append(
                InlineImage(
                    alt_text=match.group("alttext"),
                    position=Position(
                        line=line_num,
                        offset=offset,
                        length=len(string)
                    ),
                    string=string,
                    title_text=match.group("title"),
                    url=match.group("url")
                )
            )
        return result
