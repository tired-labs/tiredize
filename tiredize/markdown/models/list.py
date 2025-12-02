from dataclasses import dataclass
import typing


@dataclass(frozen=True)
class List:
    items: typing.List[str]
