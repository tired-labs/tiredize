from tiredize.types import Position
import re


def search_all_re(pattern: str, string: str) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    for match in re.finditer(pattern, string, re.VERBOSE):
        result.append(match)
    return result


def get_position_from_match(
        match: re.Match[str], text: str) -> tuple[int, int, int]:
    string = match.group()
    line_num = text[:match.start()].count("\n") + 1
    string_first_line = string.split("\n")[0]
    offset = text.split("\n")[line_num - 1].index(string_first_line)
    return line_num, offset, len(string)


def get_offset_from_position(position: Position, text: str) -> int:
    lines = text.split("\n")
    line = position.line
    if line == 1:
        return position.offset

    column = position.offset
    offset = len("\n".join(lines[0:line-1]) + "\n") + column
    return offset


def sanitize_text(pattern: str, text: str) -> str:
    """
    Replace any matches of pattern with whitespace to preserve positioning
    """
    result: str = ""
    matches = search_all_re(pattern, text)
    last_end = 0
    for match in matches:
        result += text[last_end:match.start()]
        last_end = match.end()
        old_lines = match.group().splitlines()
        new_lines: list[str] = []
        for old_line in old_lines:
            new_lines.append(" " * len(old_line))
        result += "\n".join(new_lines)
    result += text[last_end:]
    return result
