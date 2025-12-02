from dataclasses import dataclass
from tiredize.markdown.models.image import InlineImage
from tiredize.markdown.models.link import BareLink
from tiredize.markdown.models.link import BracketLink
from tiredize.markdown.models.link import InlineLink
from tiredize.markdown.models.list import List
from tiredize.markdown.models.reference import ReferenceDefinition
from tiredize.markdown.models.reference import ImageReference
from tiredize.markdown.models.reference import LinkReference
from tiredize.markdown.models.table import Table
import typing


@dataclass(frozen=False)
class Section:
    code_inline: typing.List[str]
    content: str        # This content has codeblocks/blockquotes removed
    content_raw: str    # This content has everything intact
    header_level: int
    header_title: str
    images_inline: typing.List["InlineImage"]
    images_reference: typing.List["ImageReference"]
    line_end: int
    line_start: int
    links_bare: typing.List["BareLink"]
    links_bracket: typing.List["BracketLink"]
    links_inline: typing.List["InlineLink"]
    links_reference: typing.List["LinkReference"]
    lists: typing.List["List"]
    reference_definitions: typing.List["ReferenceDefinition"]
    subsections: typing.List["Section"]
    tables: typing.List["Table"]
