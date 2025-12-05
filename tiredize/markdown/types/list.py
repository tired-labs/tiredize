from dataclasses import dataclass
import typing


@dataclass
class List:
    end: int
    items: typing.List[str]
    match: str
    start: int
    sublists: typing.List["List"]
