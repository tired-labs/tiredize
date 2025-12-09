import typing
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
from dataclasses import dataclass


@dataclass(frozen=False)
class ReferenceDefinition:
    position: Position
    string: str
    text: str
    title: str
    url: str

    RE_REFERENCE_DEFINITION = r"""
        (?<![^|\n])\[              # Start of line, but don't capture it
        (?P<text>[^]]*?)           # Capture the link text
        \]:\s+                     # Closing bracket, colon, leading spaces
        (?P<url>\S*[#\.\/]+\S*)    # Capture the URL
        \s*?                       # Optional whitespace
        ("(?P<title>[^"]*)")?      # Capture optional title
        (?=\n|$)                   # End of line or end of string
    """

    @staticmethod
    def extract(text: str) -> typing.List["ReferenceDefinition"]:
        text_sanitized = CodeBlock.sanitize(text)
        matches = search_all_re(
            ReferenceDefinition.RE_REFERENCE_DEFINITION,
            text_sanitized
        )

        result: list[ReferenceDefinition] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                ReferenceDefinition(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
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
        Replace any Reference Definitions with whitespace
        """
        return sanitize_text(ReferenceDefinition.RE_REFERENCE_DEFINITION, text)


@dataclass(frozen=False)
class LinkReference:
    position: Position
    reference: str
    string: str
    text: typing.Optional[str]

    RE_LINK_REFERENCE = r"""
        (?<!(!|\]))\[
        (\s*(?P<text>[^]]*?)\s*\]\[)?
        \s*
        (?P<reference>[^\]]+)           # Capture the URL
        \s*
        \](?!:)
        (?!\()                          # Negative lookahead to avoid links
    """

    @staticmethod
    def extract(text: str) -> typing.List["LinkReference"]:
        text_sanitized = CodeBlock.sanitize(text)
        matches = search_all_re(
            LinkReference.RE_LINK_REFERENCE,
            text_sanitized
        )

        result: list[LinkReference] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                LinkReference(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    reference=match.group("reference"),
                    string=match.group(),
                    text=match.group("text")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Link References with whitespace
        """
        return sanitize_text(LinkReference.RE_LINK_REFERENCE, text)


@dataclass(frozen=False)
class ImageReference:
    position: Position
    reference: str
    string: str
    text: typing.Optional[str]

    RE_IMAGE_REFERENCE = r"""
        !
        (?<!(\]))\[
        (\s*(?P<text>[^]]*?)\s*\]\[)?
        \s*
        (?P<reference>[^\]]+)             # Capture the URL
        \s*
        \](?!:)
    """

    @staticmethod
    def extract(text: str) -> typing.List["ImageReference"]:
        text_sanitized = CodeBlock.sanitize(text)
        matches = search_all_re(
            ImageReference.RE_IMAGE_REFERENCE,
            text_sanitized
        )

        result: list[ImageReference] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                ImageReference(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    reference=match.group("reference"),
                    string=match.group(),
                    text=match.group("text")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Image References with whitespace
        """
        return sanitize_text(ImageReference.RE_IMAGE_REFERENCE, text)
