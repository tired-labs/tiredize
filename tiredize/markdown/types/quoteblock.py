from dataclasses import dataclass
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass
class QuoteBlock:
    depth: int
    position: Position
    quote: str
    string: str

    _RE_QUOTEBLOCK = r"""
        (^|\n)             # Must be at the start of a line
        (?P<depth>[>]+)    # Capture the blockquote depth
        \s*                # Optional whitespace
        (?P<quote>[^\n]*)  # Capture anything after that as the quote
    """

    @staticmethod
    def extract(text: str) -> typing.List[QuoteBlock]:
        """
        Extract markdown quoteblocks from text.
        """
        matches = search_all_re(
            QuoteBlock._RE_QUOTEBLOCK,
            text
        )

        result: list[QuoteBlock] = []
        for match in matches:
            string = match.group().lstrip("\n").rstrip("\n")
            line_num = text[:match.start()].count("\n") + 2
            offset = text.split("\n")[line_num - 1].index(string)
            depth=len(match.group("depth"))

            if (len(result) > 0):
                line_count = result[-1].quote.count("\n") + 1
                line_end = result[-1].position.line + line_count
                if (line_num == line_end):
                    if (result[-1].depth == depth):
                        # Same level quote, append to last
                        result[-1].quote += "\n" + match.group("quote")
                        result[-1].string += match.group()
                        result[-1].position.length = len(result[-1].string)
                        continue

            result.append(
                QuoteBlock(
                    depth=len(match.group("depth")),
                    position=Position(
                        line=line_num,
                        offset=offset,
                        length=len(string)
                    ),
                    quote=match.group("quote"),
                    string=string,
                )
            )
        return result
