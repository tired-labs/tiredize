# Standard library
from __future__ import annotations
from dataclasses import dataclass

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.types.code import CodeInline
from tiredize.markdown.types.image import InlineImage
from tiredize.markdown.types.reference import ReferenceDefinition
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


@dataclass(frozen=False)
class Autolink:
    """
    An autolink per GFM 0.29-gfm section 6.8: an absolute URI or an
    email address between `<` and `>`.

    `string` is the matched text including the brackets. `url` is
    the link target: the URI as written for a URI autolink, or
    `mailto:` followed by the address for an email autolink.
    Backslashes inside the brackets are literal characters, never
    escapes.
    """
    position: Position
    string: str
    url: str

    # An absolute URI is a scheme, a colon, and any characters other
    # than ASCII whitespace, ASCII control characters, `<` and `>`.
    # A scheme is 2-32 characters: an ASCII letter, then ASCII
    # letters, digits, `+`, `.` or `-`.
    #
    # An email address is anything matching the non-normative HTML5
    # regex reproduced in the specification. Its domain labels are
    # optional (`<x@y>` is an email autolink), each label is 1-63
    # characters and may not start or end with a hyphen.
    #
    # The URI branch is tried first, so `<mailto:x@y.z>` is a URI
    # whose target is written as-is (spec example 606), while
    # `<x@y.z>` is an email whose target gains the `mailto:` prefix.
    RE_AUTOLINK = r"""
        <                                   # Opening angle bracket
        (?:
            (?P<uri>
                [A-Za-z][A-Za-z0-9+.\-]{1,31}   # Scheme, 2-32 characters
                :                               # Colon
                [^\x00-\x20\x7F<>]*             # No ASCII space/control/<>
            )
          | (?P<email>
                [a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+    # Local part
                @
                [a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?   # First label
                (?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*  # More
            )
        )
        >                                   # Closing angle bracket
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[Autolink]:
        """
        Extract autolinks from markdown text.

        Code blocks and inline code are blanked first, so a bracketed
        URI inside backticks is not a link.
        """
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        matches = search_all_re(
            Autolink.RE_AUTOLINK,
            text_sanitized
        )

        result: list[Autolink] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            uri = match.group("uri")
            if uri is not None:
                url = uri
            else:
                url = "mailto:" + match.group("email")

            result.append(
                Autolink(
                    position=position,
                    string=match.group(),
                    url=url
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Autolinks with whitespace
        """
        return sanitize_text(Autolink.RE_AUTOLINK, text)


@dataclass(frozen=False)
class ExtendedAutolink:
    position: Position
    string: str
    url: str

    RE_URL = r"""
        (?P<url>(?:http[s]?:\/\/|(?:\A|(?<=[\s\[(]))(?:\.\.\/|\.\/|\\))[^\s\])]+)
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[ExtendedAutolink]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        text_sanitized = InlineImage.sanitize(text_sanitized)
        text_sanitized = Autolink.sanitize(text_sanitized)
        text_sanitized = InlineLink.sanitize(text_sanitized)
        text_sanitized = ReferenceDefinition.sanitize(text_sanitized)
        matches = search_all_re(
            ExtendedAutolink.RE_URL,
            text_sanitized
        )

        result: list[ExtendedAutolink] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            result.append(
                ExtendedAutolink(
                    position=position,
                    string=match.group(),
                    url=match.group("url")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Extended Autolinks with whitespace
        """
        return sanitize_text(ExtendedAutolink.RE_URL, text)


@dataclass(frozen=False)
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
        (?P<url>[^\s)]+)               # Capture the URL
        (\s*?\"(?P<title>[^"]*?)\")?  # Capture optional title
        \s*\)                         # Closing parenthesis
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[InlineLink]:
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        matches = search_all_re(
            InlineLink.RE_LINK_INLINE,
            text_sanitized
        )

        result: list[InlineLink] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            result.append(
                InlineLink(
                    position=position,
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
