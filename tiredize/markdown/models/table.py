import typing


class Table:
    header: typing.List[str]
    rows: typing.List[typing.List[str]]
    start_line: int
    end_line: int
