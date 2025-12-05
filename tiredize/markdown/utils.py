import re


def search_all_re(pattern: str, string: str) -> list[re.Match[str]]:
    result: list[re.Match[str]] = []
    # for match in re.finditer(pattern, string, re.MULTILINE | re.VERBOSE):
    for match in re.finditer(pattern, string, re.VERBOSE):
        result.append(match)
    return result
