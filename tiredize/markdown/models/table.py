import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    end: int
    header: typing.List[str]
    match: str
    rows: typing.List[typing.List[str]]
    start: int
