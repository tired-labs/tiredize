from dataclasses import dataclass
from tiredize.types import Position


@dataclass(frozen=True)
class CodeBlock:
    content: str
    position: Position
    syntax: str

    RE_CODEBLOCK = r"""
        ^                     # Must be at the start of a line
        (?P<delimiter>``[`]+) # Opening backticks (three or more)
        (?P<syntax>.*)        # Capture the syntax if present
        $                     # Line ends here
    """


@dataclass(frozen=True)
class CodeInline:
    content: str
    end: int
    start: int

    RE_CODE_INLINE = r"""
        [^\S\s^]?    # Exclude any characters before the backtick
        `            # Opening backtick
        [^\n`]+      # Capture anything except backtick or newline
        `            # Closing backtick
    """
