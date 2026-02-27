# Standard library
from __future__ import annotations
from dataclasses import dataclass

# Local
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


@dataclass(frozen=False)
class QuoteBlock:
    depth: int
    position: Position
    quote: str
    string: str

    RE_QUOTEBLOCK = r"""
        (?<![^|\n])        # Start of line, but don't capture it
        (?P<depth>[>]+)    # Capture the blockquote depth
        \s*                # Optional whitespace
        (?P<quote>[^\n]*)  # Capture anything after that as the quote
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[QuoteBlock]:
        text_sanitized = CodeBlock.sanitize(text)
        matches = search_all_re(QuoteBlock.RE_QUOTEBLOCK, text_sanitized)

        result: list[QuoteBlock] = []
        prev_end_local: int | None = None

        for match in matches:
            depth = len(match.group("depth"))
            start_local = match.start()
            end_local = match.end()

            # Handle continued quotes
            if result and prev_end_local is not None:
                between = text_sanitized[prev_end_local:start_local]

                is_next_line = between == "\n" or between == "\r\n"
                if is_next_line and result[-1].depth == depth:
                    result[-1].quote += "\n" + match.group("quote")
                    result[-1].string += "\n" + match.group()
                    new_length = result[-1].position.length
                    new_length += (end_local - start_local)
                    new_length += len(between)
                    result[-1].position = Position(
                        offset=result[-1].position.offset,
                        length=new_length,
                    )

                    prev_end_local = end_local
                    continue

            position = Position(
                offset=base_offset + start_local,
                length=end_local - start_local,
            )
            result.append(
                QuoteBlock(
                    depth=depth,
                    position=position,
                    quote=match.group("quote"),
                    string=match.group(),
                )
            )
            prev_end_local = end_local

        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any QuoteBlocks with whitespace
        """
        return sanitize_text(QuoteBlock.RE_QUOTEBLOCK, text)
