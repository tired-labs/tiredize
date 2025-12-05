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
import typing


@dataclass(frozen=False)
class Section:
    code_block: typing.List["CodeBlock"]
    code_inline: typing.List["CodeInline"]
    content_raw: str    # This content has everything intact
    content: str        # This content has codeblocks/blockquotes removed
    header: "Header"
    images_inline: typing.List["InlineImage"]
    images_reference: typing.List["ImageReference"]
    line_end: int
    line_start: int
    links_bare: typing.List["BareLink"]
    links_bracket: typing.List["BracketLink"]
    links_inline: typing.List["InlineLink"]
    links_reference: typing.List["LinkReference"]
    lists: typing.List["List"]
    quoteblocks: typing.List["QuoteBlock"]
    reference_definitions: typing.List["ReferenceDefinition"]
    subsections: typing.List["Section"]
    tables: typing.List["Table"]
