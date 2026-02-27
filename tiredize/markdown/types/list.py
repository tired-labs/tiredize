# Standard library
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=False)
class List:
    end: int
    items: list[str]
    match: str
    start: int
    sublists: list[List]

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[List]:
        if len(text) == 0:
            return []
        result: list[List] = []
        return result
