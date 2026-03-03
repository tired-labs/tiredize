# Standard library
from __future__ import annotations
from dataclasses import dataclass

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.types.code import CodeInline
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


@dataclass(frozen=False)
class InlineImage:
    text: str
    position: Position
    string: str
    title: str | None
    url: str

    RE_INLINE_IMAGE = r"""
        !\[                           # Opening (exclamation mark and bracket)
        \s*                           # Optional whitespace
        (?P<text>[^]]*?)              # Capture the title
        \s*                           # Optional whitespace
        \]\(                          # Closing bracket, opening parenthesis
        \s*                           # Optional whitespace
        (?P<url>[^\s)]+)               # Capture the URL
        (\s*?\"(?P<title>[^"]*?)\")?  # Capture optional title
        \s*\)                         # Closing parenthesis
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[InlineImage]:
        """
        Extract markdown images from text.
        """
        text_sanitized = CodeBlock.sanitize(text)
        text_sanitized = CodeInline.sanitize(text_sanitized)
        matches = search_all_re(
            InlineImage.RE_INLINE_IMAGE,
            text_sanitized
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
