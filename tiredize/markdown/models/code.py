from dataclasses import dataclass


@dataclass(frozen=True)
class CodeBlock:
    syntax: str
    content: str
    end: int
    start: int


@dataclass(frozen=True)
class CodeInline:
    content: str
    end: int
    start: int
