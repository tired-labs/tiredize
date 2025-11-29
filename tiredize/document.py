from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import yaml

# Regular expressions reused across parsing
RE_FRONT_MATTER_YAML_DELIM = r"^---$"
RE_HEADER = re.compile(
    r"^(?P<hashes>#{1,6})\s(?P<title>.+?)$",
    re.MULTILINE
)
RE_CODE_FENCE = re.compile(r"^``[`]+.*$")
RE_CODE_INLINE = re.compile(r"`[^`]*`")
RE_LINK_INLINE = re.compile(
    r"(?P<image>!?)"
    r"\["
    r"(?P<title>.*?)"
    r"\]\("
    r"(?P<url>\s*\S+)"
    r"\s*?"
    r"\)"
)
RE_LINK_REFERENCE = re.compile(
    r"\["
    r"(?P<title>[^^].*]?)"
    r"\]: "
    r"(?P<url>\s*\S*[\.\/]+\S*)"
    r"[\s]*?"
    r"(?P<desc>([\"\(\'].*[\"\'\)])*)",
    re.MULTILINE
)
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
    is_inline: bool
    is_reference: bool
    line: int
    url: str
    title: Optional[str] = None


@dataclass
class Document:
    """Parsed view of a markdown document."""

    # The body text (without front matter)
    body: str

    # Set of 1-based line numbers that are inside fenced code blocks
    fenced_lines: set[int]

    # The parsed front matter as a dict
    front_matter: Dict[str, str]

    # Extracted elements
    headings: List[Heading]

    # The body split into lines
    lines: List[str]

    # Extracted links
    links: List[Link]

    # The original source path (if any)
    path: Optional[Path]

    # Extracted tables
    tables: List[Table]

    # The full original text of the document
    text: str

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
        links = _extract_links_and_images(body, fenced_lines)

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


def _split_front_matter(text: str) -> Tuple[Dict[str, str], str]:
    """
    Split YAML front matter from the rest of the document.

    Returns (front_matter_dict, body_text).
    If no front matter is present, front_matter is {} and body is original
    text.
    """

    split = re.split(
        RE_FRONT_MATTER_YAML_DELIM,
        text,
        maxsplit=2,
        flags=re.MULTILINE
    )

    # If there isn't 3 parts, there is no valid front matter
    if len(split) < 3:
        return {}, text

    # If the first part isn't empty, we encountered unexpected text beforehand
    if len(split[0]) > 0:
        return {}, text

    # Try to parse the second part as YAML
    yaml_block = None
    try:
        yaml_block = yaml.safe_load(split[1])
    except yaml.YAMLError:
        raise ValueError(f"Invalid YAML in frontmatter: {split[1]!r}")

    # If we made it here, we have valid front matter
    return yaml_block, split[2]


def _get_fenced_lines(text: str) -> set[int]:
    """
    Identify all line numbers that are inside fenced code blocks.

    Includes the fence lines themselves.
    """
    fenced: set[int] = set()
    in_code: bool = False
    delimiter: str = "```"

    # Scan through all lines to find any that match the code fence regex
    for i, line in enumerate(text.splitlines(), start=1):

        # if we are already in a code block, mark this line
        if in_code:
            fenced.add(i)

            # if this line is the matching delimiter, we exit code block
            if line.startswith(delimiter):
                in_code = not in_code
            continue

        # if this is the start of a codeblock, store the closing delimiter
        if RE_CODE_FENCE.match(line):
            in_code = not in_code
            fenced.add(i)
            delimiter = "`" * line.count("`")
            continue

    return fenced


def _extract_headings(text: str, fenced_lines: set[int]) -> List[Heading]:
    """Return all headings as Heading objects, ignoring fenced code blocks."""

    headings: List[Heading] = []

    for line_no, line in enumerate(text.splitlines(), start=1):

        # Ignore headings that appear inside fenced code
        if line_no in fenced_lines:
            continue

        # Check if this line is a heading
        m = RE_HEADER.match(line)
        if not m:
            continue

        # Extract level/title and save it to the results
        level = len(m.group("hashes"))
        title = m.group("title").strip()
        headings.append(Heading(level=level, title=title, line=line_no))

    return headings


def _split_table_row(line: str) -> List[str]:
    """
    Split a markdown table row into cell texts.

    Keeps empty cells intact, strips outer pipes and whitespace.
    """
    # Remove leading/trailing pipe if present
    s = line.rstrip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]

    cells: List[str] = []
    cell = ""
    escaped = False

    # Parse the row character by character to handle escaped pipes
    for i in s:

        # Handle unescaped pipe as cell separator
        if (not escaped) and (i == "|"):
            cells.append(cell.strip())
            cell = ""
            continue

        # Otherwise, add character to current cell
        cell += i

        # Handle escape character
        if i == "\\":
            escaped = True
            continue

        # Reset escape state
        escaped = False

    # Add the last cell
    cells.append(cell.strip())
    return cells


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

        # Start collecting a table
        block: List[Tuple[int, str]] = []

        # Collect a contiguous block of table lines, all outside fenced code
        while i < len(lines):
            line_no = i + 1

            # Stop if we hit fenced code or a non-table row
            if line_no in fenced_lines or not RE_TABLE_ROW.match(lines[i]):
                break

            # Ignore tables without a divider as second row
            if len(block) == 1 and not RE_TABLE_DIV.match(lines[i]):
                break

            # Add this line to the current table block
            block.append((line_no, lines[i]))
            i += 1

        # Ignore tables that are too short to be valid
        if len(block) < 2:
            continue

        # Parse the header row
        header_line_no, header_line = block[0]
        header = _split_table_row(header_line)

        # Parse the body rows that come after the divider row
        body_rows: List[List[str]] = []
        data_block = block[2:]

        # Parse each data row
        for _, row_text in data_block:
            body_rows.append(_split_table_row(row_text))

        # Store the parsed table
        tables.append(
            Table(
                header=header,
                rows=body_rows,
                start_line=header_line_no,
                end_line=block[-1][0],
            )
        )

    return tables


def _extract_links_and_images(text: str, fenced_lines: set[int]) -> List[Link]:
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

        # Skip lines inside fenced code
        if i in fenced_lines:
            continue

        # Remove inline code spans to avoid false positives
        search_line = RE_CODE_INLINE.sub("", line)

        for m in RE_LINK_INLINE.findall(search_line):
            if m[0] == "!":
                # TODO: Store images as well
                # print(f"IMAGE: [{m[1]}] ------------ {m[2]} at line {i}")
                continue
            else:
                links.append(
                    Link(
                        is_inline=True,
                        is_reference=False,
                        url=m[2].strip(),
                        title=m[1].strip(),
                        line=i,
                    )
                )

        for m in RE_LINK_REFERENCE.findall(search_line):
            links.append(
                Link(
                    is_inline=False,
                    is_reference=True,
                    url=m[1].strip(),
                    title=m[0].strip(),
                    line=i,
                )
            )

    return links
