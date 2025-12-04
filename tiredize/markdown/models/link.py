from dataclasses import dataclass


@dataclass(frozen=True)
class BareLink:
    end: int
    match: str
    start: int
    url: str


@dataclass(frozen=True)
class BracketLink:
    end: int
    match: str
    start: int
    url: str


@dataclass(frozen=True)
class InlineLink:
    end: int
    match: str
    start: int
    title: str
    url: str
