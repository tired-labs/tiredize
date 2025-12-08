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
from tiredize.markdown.utils import get_offset_from_position
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

    @staticmethod
    def extract(text: str) -> typing.List["Section"]:
        """
        Extract sections from markdown.
        """
        result: typing.List[Section] = []

        md_sanitized = CodeBlock.sanitize(text)
        headers = Header.extract(md_sanitized)
        if len(headers) == 0:
            return result

        for i, header in enumerate(headers, start=0):
            offset_start: int = 0
            offset_end: int = 0
            offset_start = get_offset_from_position(header.position, text)
            if i + 1 < len(headers):
                offset_end = get_offset_from_position(
                    headers[i + 1].position,
                    text
                )
            else:
                offset_end = len(text)
            section_text = text[offset_start:offset_end]

            new_section = Section(
                code_block=CodeBlock.extract(section_text),
                code_inline=CodeInline.extract(section_text),
                header=header,
                images_inline=InlineImage.extract(section_text),
                images_reference=ImageReference.extract(section_text),
                links_bare=BareLink.extract(section_text),
                links_bracket=BracketLink.extract(section_text),
                links_inline=InlineLink.extract(section_text),
                links_reference=LinkReference.extract(section_text),
                lists=List.extract(section_text),
                position=Position(
                    line=header.position.line,
                    offset=header.position.offset,
                    length=len(section_text),
                ),
                quoteblocks=QuoteBlock.extract(section_text),
                reference_definitions=ReferenceDefinition.extract(
                    section_text),
                string=section_text,
                string_safe=CodeBlock.sanitize(section_text),
                subsections=[],
                tables=Table.extract(section_text),
            )
            result.append(new_section)

        return result
