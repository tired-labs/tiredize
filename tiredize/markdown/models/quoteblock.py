from dataclasses import dataclass
import typing


@dataclass(frozen=True)
class QuoteBlock:
    content: str
    end: int
    quoteblocks: typing.List["QuoteBlock"]
    start: int
    syntax: str
