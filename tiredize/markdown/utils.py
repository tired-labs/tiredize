import re


def search_all_re(pattern: str, string: str) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    # for match in re.finditer(pattern, string, re.MULTILINE | re.VERBOSE):
    for match in re.finditer(pattern, string, re.VERBOSE):
        result.append(match)
    return result


def get_position_from_match(
        match: re.Match[str], text: str) -> tuple[int, int, int]:
    string = match.group()
    line_num = text[:match.start()].count("\n") + 1
    if string.startswith("\n"):
        string = string.lstrip("\n")
        line_num += 1
    string_first_line = string.split("\n")[0]
    offset = text.split("\n")[line_num - 1].index(string_first_line)
    return line_num, offset, len(string)
