import typing
from dataclasses import dataclass


@dataclass(frozen=True)
class Table:
    end: int
    header: typing.List[str]
    match: str
    rows: typing.List[typing.List[str]]
    start: int


# RE_TABLE_DIV = re.compile(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$")
# RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
