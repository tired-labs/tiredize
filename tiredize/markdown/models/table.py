import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    header: typing.List[str]
    rows: typing.List[typing.List[str]]
    start_line: int
    end_line: int
