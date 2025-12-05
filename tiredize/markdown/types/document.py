from dataclasses import dataclass
from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.markdown.types.section import Section
import typing


@dataclass
class Document:
    frontmatter: typing.Optional[FrontMatter] = None
    sections: typing.Optional[typing.List[Section]] = []
