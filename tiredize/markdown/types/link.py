from dataclasses import dataclass
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.types.code import CodeInline
from tiredize.markdown.types.image import InlineImage
from tiredize.markdown.types.quoteblock import QuoteBlock
from tiredize.markdown.types.reference import ReferenceDefinition
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass
class BareLink:
    position: Position
    string: str
    url: str

    RE_URL = r"""
        (?P<url>(https+:\/\/|(./|\\))\S+)  # Capture the URL
    """

    @staticmethod
    def extract(text: str) -> typing.List["BareLink"]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        text_sanitized = QuoteBlock.sanitize(text_sanitized)
        text_sanitized = InlineImage.sanitize(text_sanitized)
        text_sanitized = BracketLink.sanitize(text_sanitized)
        text_sanitized = InlineLink.sanitize(text_sanitized)
        text_sanitized = ReferenceDefinition.sanitize(text_sanitized)
        matches = search_all_re(
            BareLink.RE_URL,
            text_sanitized
        )

        result: list[BareLink] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                BareLink(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group(),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Bare Links with whitespace
        """
        return sanitize_text(BareLink.RE_URL, text)


@dataclass
class BracketLink:
    position: Position
    string: str
    url: str

    RE_LINK_BRACKET = r"""
        <                            # Opening angle bracket
        (?P<url>https?:\/\/\S+)      # Capture the URL
        >                            # Closing angle bracket
    """

    @staticmethod
    def extract(text: str) -> typing.List["BracketLink"]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        text_sanitized = QuoteBlock.sanitize(text_sanitized)
        matches = search_all_re(
            BracketLink.RE_LINK_BRACKET,
            text_sanitized
        )

        result: list[BracketLink] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                BracketLink(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group(),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Bracket Links with whitespace
        """
        return sanitize_text(BracketLink.RE_LINK_BRACKET, text)


@dataclass
class InlineLink:
    position: Position
    string: str
    title: str
    url: str

    RE_LINK_INLINE = r"""
        (?<!!)                        # Negative lookbehind to avoid images
        \[\s*                         # Opening bracket and whitespace
        (?P<text>[^]]*?)              # Capture the title
        \s*                           # Optional whitespace
        \]\(                          # Closing bracket, opening parenthesis
        \s*                           # Optional whitespace
        (?P<url>\S+)                  # Capture the URL
        (\s*?\"(?P<title>[^"]*?)\")?  # Capture optional title
        \s*\)                         # Closing parenthesis
    """

    @staticmethod
    def extract(text: str) -> typing.List["InlineLink"]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        text_sanitized = QuoteBlock.sanitize(text_sanitized)
        matches = search_all_re(
            InlineLink.RE_LINK_INLINE,
            text_sanitized
        )

        result: list[InlineLink] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)
            result.append(
                InlineLink(
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
                    string=match.group(),
                    title=match.group("title"),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Inline Links with whitespace
        """
        return sanitize_text(InlineLink.RE_LINK_INLINE, text)
