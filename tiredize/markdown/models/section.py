from dataclasses import dataclass
import typing


@dataclass(frozen=False)
class Section:
    content: str
    header_level: int
    header_title: str
    line_end: int
    line_start: int
    subsections: typing.List["Section"]
