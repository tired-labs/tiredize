# Standard library
from __future__ import annotations
from dataclasses import dataclass

# Local
from tiredize.core_types import Position
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


@dataclass(frozen=False)
class Table:
    divider: list[str]
    header: list[str]
    position: Position
    rows: list[list[str]]
    string: str

    RE_TABLE = r"""
        (?P<header>
            [|]?
            ([^\n|]*[|])*
            [^\n|]+
            [|]?
            \n
        )
        (?P<divider>
            [|][ \t]*:?-+:?[ \t]*
            ([|][ \t]*:?-+:?[ \t]*)*
            [|]?\n
            |
            [ \t]*:?-+:?[ \t]*
            ([|][ \t]*:?-+:?[ \t]*)+
            [|]?\n
        )
        (?P<rows>([^\n]+(\n|$))*)
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[Table]:
        """
        Extract table from markdown text.
        """
        matches = search_all_re(
            Table.RE_TABLE,
            text
        )

        result: list[Table] = []
        for match in matches:
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            header = match.group("header")
            header = header.strip()
            header = header[:-1] if header[-1] == "|" else header
            header = header[1:] if header[0] == "|" else header
            header = header.split("|")
            header = [cell.strip() for cell in header]

            divider = match.group("divider")
            divider = divider.strip()
            divider = divider[:-1] if divider[-1] == "|" else divider
            divider = divider[1:] if divider[0] == "|" else divider
            divider = divider.split("|")
            divider = [cell.strip() for cell in divider]

            rows: list[list[str]] = []
            row_matches = match.group("rows").splitlines()
            for row in row_matches:
                row = row.strip()
                row = row[:-1] if row[-1] == "|" else row
                row = row[1:] if row[0] == "|" else row
                row = row.split("|")
                row = [cell.strip() for cell in row]
                rows.append(row)

            result.append(
                Table(
                    divider=divider,
                    header=header,
                    position=position,
                    rows=rows,
                    string=match.group()
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Tables with whitespace
        """
        return sanitize_text(Table.RE_TABLE, text)
