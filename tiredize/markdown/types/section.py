from dataclasses import dataclass
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.types.code import CodeInline
from tiredize.markdown.types.header import Header
from tiredize.markdown.types.image import InlineImage
from tiredize.markdown.types.link import BareLink
from tiredize.markdown.types.link import BracketLink
from tiredize.markdown.types.link import InlineLink
from tiredize.markdown.types.list import List
from tiredize.markdown.types.quoteblock import QuoteBlock
from tiredize.markdown.types.reference import ImageReference
from tiredize.markdown.types.reference import LinkReference
from tiredize.markdown.types.reference import ReferenceDefinition
from tiredize.markdown.types.table import Table
from tiredize.types import Position
import typing


@dataclass(frozen=False)
class Section:
    code_block: typing.List["CodeBlock"]
    code_inline: typing.List["CodeInline"]
    header: "Header"
    images_inline: typing.List["InlineImage"]
    images_reference: typing.List["ImageReference"]
    links_bare: typing.List["BareLink"]
    links_bracket: typing.List["BracketLink"]
    links_inline: typing.List["InlineLink"]
    links_reference: typing.List["LinkReference"]
    lists: typing.List["List"]
    position: Position
    quoteblocks: typing.List["QuoteBlock"]
    reference_definitions: typing.List["ReferenceDefinition"]
    string: str
    string_safe: str
    subsections: typing.List["Section"]
    tables: typing.List["Table"]

    def extract(text: str) -> typing.List["Section"]:
        """
        Extract sections from markdown.
        """
        result: typing.List[Section] = []

        # md_sanitized = CodeBlock.sanitize(text)
        # headers = Header.extract(md_sanitized)
        # if len(headers) == 0:
        #     return result

        # text_lines = text.splitlines()
        # for i, header in enumerate(headers, start=0):
        #     line_num = header.position.line - 1
        #     new_text_lines = "\n".join(text_lines[line_num:])
        #     if  i + 1 == len(headers):
        #         new_text_end = headers[i+1].line
        #         line_num = header.position.line - 1

        #         next_line_num = next_header.position.line - 1
        #         new_text_lines = "\n".join(
        #             text_lines[line_num:next_line_num]
        #         )

        # md_sanitized_start = md_sanitized.split("\n", maxsplit=line_num)
        # if len(md_sanitized_start) > 1:
        #     md_sanitized = "\n".join(md_sanitized_start[1:])
        # else:
        #     md_sanitized = md_sanitized[0]

        return result
