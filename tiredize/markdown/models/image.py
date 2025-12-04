import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class InlineImage:
    alt_text: str
    end: int
    start: int
    title_text: typing.Optional[str]
    url: str
