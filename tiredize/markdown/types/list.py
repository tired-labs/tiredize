from dataclasses import dataclass
import typing


@dataclass(frozen=False)
class List:
    end: int
    items: typing.List[str]
    match: str
    start: int
    sublists: typing.List["List"]

    @staticmethod
    def extract(text: str) -> typing.List["List"]:
        if len(text) == 0:
            return []
        result: typing.List[List] = []
        return result
