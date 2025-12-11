from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing


@dataclass(frozen=False)
class Table:
    divider: typing.List[str]
    header: typing.List[str]
    position: Position
    rows: typing.List[typing.List[str]]
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
            [|]?
            ([ \t]*:?-+:?[ \t]*[|]?)*
            [|]
            ([ \t]*:?-+:?[ \t]*[|]?)*
            \n
        )
        (?P<rows>([^\n]+(\n|$))*)
    """

    @staticmethod
    def extract(text: str) -> typing.List["Table"]:
        """
        Extract table from markdown text.
        """
        matches = search_all_re(
            Table.RE_TABLE,
            text
        )

        result: list[Table] = []
        for match in matches:
            line_num, offset, length = get_position_from_match(match, text)

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

            rows: typing.List[typing.List[str]] = []
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
                    position=Position(
                        length=length,
                        line=line_num,
                        offset=offset
                    ),
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
