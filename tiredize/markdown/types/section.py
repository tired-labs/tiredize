from dataclasses import dataclass
from tiredize.core_types import Position
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
    def extract(text: str, base_offset: int = 0) -> typing.List["Section"]:
        """
        Extract sections from markdown.
        """
        result: typing.List[Section] = []

        headers = Header.extract(text=text, base_offset=base_offset)
        if len(headers) == 0:
            position = Position(
                offset=base_offset,
                length=len(text)
            )
            section = Section._extract(
                text,
                position,
                base_offset=position.offset,
            )
            return [section]

        for i, position in enumerate([header.position for header in headers]):
            offset_start = position.offset - base_offset
            if i + 1 == len(headers):
                offset_end = len(text)
            else:
                offset_end = headers[i + 1].position.offset - base_offset
            position = Position(
                offset=base_offset + offset_start,
                length=offset_end - offset_start
            )
            section = Section._extract(
                text[offset_start:offset_end],
                position,
                base_offset=position.offset,
            )
            result.append(section)
        Section._map_subsections(result)
        return result

    @staticmethod
    def _extract(
        string: str,
        position: Position,
        base_offset: int = 0
    ) -> "Section":

        header = None
        headers = Header.extract(text=string, base_offset=base_offset)
        if len(headers) >= 1:
            header = headers[0]
        else:
            header = Header(
                level=0,
                position=Position(offset=base_offset, length=0),
                slug="",
                string="",
                title=""
            )

        section = Section(
            code_block=CodeBlock.extract(
                text=string,
                base_offset=base_offset
            ),
            code_inline=CodeInline.extract(
                text=string,
                base_offset=base_offset
            ),
            header=header,
            images_inline=InlineImage.extract(
                text=string,
                base_offset=base_offset
            ),
            images_reference=ImageReference.extract(
                text=string,
                base_offset=base_offset
            ),
            links_bare=BareLink.extract(
                text=string,
                base_offset=base_offset
            ),
            links_bracket=BracketLink.extract(
                text=string,
                base_offset=base_offset
            ),
            links_inline=InlineLink.extract(
                text=string,
                base_offset=base_offset
            ),
            links_reference=LinkReference.extract(
                text=string,
                base_offset=base_offset
            ),
            lists=List.extract(
                text=string,
                base_offset=base_offset
            ),
            position=position,
            quoteblocks=QuoteBlock.extract(
                text=string,
                base_offset=base_offset
            ),
            reference_definitions=ReferenceDefinition.extract(
                text=string,
                base_offset=base_offset
            ),
            string=string,
            string_safe=CodeBlock.sanitize(
                CodeInline.sanitize(string)
            ),
            subsections=[],
            tables=Table.extract(
                text=string,
                base_offset=base_offset
            )
        )
        return section

    @staticmethod
    def _map_subsections(sections: typing.List["Section"]) -> None:
        i = 0
        next_i = i + 1
        while len(sections) > i:
            while len(sections) > next_i:
                if sections[i].header.level == 0:
                    break
                if sections[i].header.level < sections[next_i].header.level:
                    sections[i].subsections.append(sections[next_i])
                    next_i += 1
                else:
                    break
            i += 1
            next_i = i + 1
