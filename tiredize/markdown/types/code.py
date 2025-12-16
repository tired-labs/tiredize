from dataclasses import dataclass
from tiredize.core_types import Position
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
import typing


@dataclass(frozen=False)
class CodeBlock:
    code: str
    delimiter: str
    language: str
    position: Position
    string: str

    RE_CODEBLOCK = r"""
        (?<![^|\n])
        (?P<delimiter>``[`]+)
        (?P<language>.*)
        \n
        (?P<code>[\s\S]*?)
        \n
        \1
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> typing.List["CodeBlock"]:
        """
        Extract fenced codeblocks from markdown text.
        """
        matches = search_all_re(
            CodeBlock.RE_CODEBLOCK,
            text
        )

        result: list[CodeBlock] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )
            result.append(
                CodeBlock(
                    code=match.group("code"),
                    delimiter=match.group("delimiter"),
                    language=match.group("language"),
                    position=position,
                    string=match.group()
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Code Blocks with whitespace
        """
        return sanitize_text(CodeBlock.RE_CODEBLOCK, text)


@dataclass(frozen=False)
class CodeInline:
    code: str
    position: Position
    string: str

    RE_CODE_INLINE = r"""
        `                  # Opening backtick
        (?P<code>[^\n`]+)  # Capture anything except backtick or newline
        `                  # Closing backtick
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> typing.List["CodeInline"]:
        """
        Extract inline code from markdown text.
        """
        matches = search_all_re(
            CodeInline.RE_CODE_INLINE,
            text
        )

        result: list[CodeInline] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )
            result.append(
                CodeInline(
                    position=position,
                    string=match.group(),
                    code=match.group("code")
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Code Inlines with whitespace
        """
        return sanitize_text(CodeInline.RE_CODE_INLINE, text)
