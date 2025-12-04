from dataclasses import dataclass


@dataclass(frozen=True)
class Header:
    title: str
    end: int
    level: int
    start: int
