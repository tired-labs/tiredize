from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import yaml

# Regular expressions reused across parsing
RE_FRONT_MATTER_DELIM = re.compile(r"^---\s*$")
RE_HEADER = re.compile(
    r"^(?P<hashes>#{1,6})\s(?P<title>.+?)$",
    re.MULTILINE,
)
RE_CODE_FENCE = re.compile(r"^\s*```")
RE_CODE_INLINE = re.compile(r"`[^`]*`")
RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
RE_TABLE_DIV = re.compile(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$")
RE_URL = re.compile(r"https?://\S+")


@dataclass(frozen=True)
class Heading:
    level: int
    title: str
    line: int


@dataclass(frozen=True)
class Table:
    header: List[str]
    rows: List[List[str]]
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Link:
    url: str
    line: int
    is_global: bool


@dataclass
class Document:
    """Parsed view of a markdown document."""

    path: Optional[Path]
    text: str

    front_matter: Dict
    body: str
    lines: List[str]

    fenced_lines: set[int]
    headings: List[Heading]
    tables: List[Table]
    links: List[Link]

    @classmethod
    def from_path(cls, path: Path) -> "Document":
        text = path.read_text(encoding="utf-8")
        return cls.from_text(text=text, path=path)

    @classmethod
    def from_text(cls, text: str, path: Optional[Path] = None) -> "Document":
        front_matter, body = _split_front_matter(text)
        lines = body.splitlines()

        fenced_lines = _get_fenced_lines(body)
        headings = _extract_headings(body, fenced_lines)
        tables = _extract_tables(body, fenced_lines)
        links = _extract_links(body, fenced_lines)

        return cls(
            path=path,
            text=text,
            front_matter=front_matter,
            body=body,
            lines=lines,
            fenced_lines=fenced_lines,
            headings=headings,
            tables=tables,
            links=links,
        )

    def line_at(self, line_no: int) -> str:
        """Return the raw line text for a given 1 based line number."""
        if 1 <= line_no <= len(self.lines):
            return self.lines[line_no - 1]
        return ""


def _split_front_matter(text: str) -> Tuple[Dict, str]:
    """
    Split YAML front matter from the rest of the document.

    Returns (front_matter_dict, body_text).
    If no front matter is present, front_matter is {} and body is original
    text.
    """
    lines = text.splitlines()
    if not lines:
        return {}, text

    if not RE_FRONT_MATTER_DELIM.match(lines[0]):
        return {}, text

    # Find the closing delimiter
    for i in range(1, len(lines)):
        if RE_FRONT_MATTER_DELIM.match(lines[i]):
            yaml_block = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            data = yaml.safe_load(yaml_block) or {}
            if not isinstance(data, dict):
                # Defensive: malformed front matter should not crash parsing
                data = {}
            return data, body

    # No closing delimiter, treat as no front matter
    return {}, text


def _get_fenced_lines(text: str) -> set[int]:
    """
    Identify all line numbers that are inside fenced code blocks.

    Includes the fence lines themselves.
    """
    fenced: set[int] = set()
    in_code = False
    for i, line in enumerate(text.splitlines(), start=1):
        if RE_CODE_FENCE.match(line):
            fenced.add(i)
            in_code = not in_code
            continue
        if in_code:
            fenced.add(i)
    return fenced


def _extract_headings(text: str, fenced_lines: set[int]) -> List[Heading]:
    """Return all headings as Heading objects, ignoring fenced code blocks."""
    headings: List[Heading] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in fenced_lines:
            # Ignore headings that appear inside fenced code
            continue

        m = RE_HEADER.match(line)
        if not m:
            continue

        level = len(m.group("hashes"))
        title = m.group("title").strip()

        headings.append(Heading(level=level, title=title, line=line_no))

    return headings


def _split_table_row(line: str) -> List[str]:
    """
    Split a markdown table row into cell texts.

    Keeps empty cells intact, strips outer pipes and whitespace.
    """
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [cell.strip() for cell in s.split("|")]


def _extract_tables(text: str, fenced_lines: set[int]) -> List[Table]:
    """
    Extract simple GitHub style markdown tables.

    Tables are contiguous blocks of lines that match RE_TABLE_ROW,
    excluding any lines inside fenced code blocks.
    """
    tables: List[Table] = []
    lines = text.splitlines()
    i = 0

    while i < len(lines):
        line_no = i + 1

        # Skip lines that are inside fenced code or not table rows
        if line_no in fenced_lines or not RE_TABLE_ROW.match(lines[i]):
            i += 1
            continue

        block: List[Tuple[int, str]] = []

        # Collect a contiguous block of table lines, all outside fenced code
        while i < len(lines):
            line_no = i + 1
            if line_no in fenced_lines or not RE_TABLE_ROW.match(lines[i]):
                break
            block.append((line_no, lines[i]))
            i += 1

        if len(block) < 2:
            # Too small to be a valid table
            continue

        header_line_no, header_line = block[0]
        header = _split_table_row(header_line)

        body_rows: List[List[str]] = []
        data_block = block[1:]

        # Skip the separator row if present
        if data_block and RE_TABLE_DIV.match(data_block[0][1].strip()):
            data_block = data_block[1:]

        for _, row_text in data_block:
            body_rows.append(_split_table_row(row_text))

        tables.append(
            Table(
                header=header,
                rows=body_rows,
                start_line=header_line_no,
                end_line=block[-1][0],
            )
        )

    return tables


def _extract_links(text: str, fenced_lines: set[int]) -> List[Link]:
    """
    Extract URLs from the document body, skipping fenced code.

    For now, global link detection is simple:
      a line is considered a global link definition if it looks like:
        [label]: url
      or a reference style variant.
    """
    links: List[Link] = []
    lines = text.splitlines()

    for i, line in enumerate(lines, start=1):
        if i in fenced_lines:
            continue

        search_line = RE_CODE_INLINE.sub("", line)

        # Global link definition style
        # For now reuse a simple heuristic: starts with '[' and contains ']:'
        is_global_def = search_line.lstrip()
        is_global_def = is_global_def.startswith("[") and "]: " in search_line

        for m in RE_URL.finditer(search_line):
            url = m.group(0)
            links.append(
                Link(
                    url=url,
                    line=i,
                    is_global=is_global_def,
                )
            )

    return links
