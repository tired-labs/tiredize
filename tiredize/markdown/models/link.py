from dataclasses import dataclass


@dataclass(frozen=True)
class BareLink:
    end: int
    start: int
    url: str


@dataclass(frozen=True)
class BracketLink:
    end: int
    start: int
    url: str


@dataclass(frozen=True)
class InlineLink:
    end: int
    start: int
    title: str
    url: str
