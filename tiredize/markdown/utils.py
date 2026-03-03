# Standard library
from __future__ import annotations
import re


def search_all_re(pattern: str, string: str) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    for match in re.finditer(pattern, string, re.VERBOSE):
        result.append(match)
    return result


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
        old_lines = match.group().split("\n")
        new_lines: list[str] = []
        for old_line in old_lines:
            new_lines.append(" " * len(old_line))
        result += "\n".join(new_lines)
    result += text[last_end:]
    return result
