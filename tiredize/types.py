from dataclasses import dataclass


@dataclass(frozen=False)
class Position:
    line: int
    offset: int
    length: int
