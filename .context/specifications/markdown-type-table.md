# Specification: Table

**GFM Equivalent:** Tables (GFM spec section 4.10, GFM extension)
**Source File:** `tiredize/markdown/types/table.py`
**GFM Compliance:** Partial

## Description

A GFM table consists of a header row, a divider row (containing
dashes and optional colons for alignment), and zero or more data
rows. Cells are separated by pipe characters. The parser extracts
the header, divider, and rows as structured lists of strings.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `divider` | `list[str]` | Divider cells (stripped of pipes and whitespace) |
| `header` | `list[str]` | Header cells (stripped of pipes and whitespace) |
| `position` | `Position` | Character offset and length relative to document root |
| `rows` | `list[list[str]]` | Data rows, each a list of cell strings |
| `string` | `str` | The full matched text |

## Regex Pattern

```
(?P<header>             # Header row:
    [|]?                #   Optional leading pipe
    ([^\n|]*[|])*       #   Zero or more cells followed by pipe
    [^\n|]+             #   Final cell (no trailing pipe required)
    [|]?                #   Optional trailing pipe
    \n                  #   Newline
)
(?P<divider>            # Divider row (two alternatives):
    [|][ \t]*:?-+:?[ \t]*       # Alt 1: starts with pipe
    ([|][ \t]*:?-+:?[ \t]*)*    #   more pipe-separated cells
    [|]?\n                       #   optional trailing pipe + newline
    |                            # -- OR --
    [ \t]*:?-+:?[ \t]*          # Alt 2: starts without pipe
    ([|][ \t]*:?-+:?[ \t]*)+    #   one or more pipe-separated cells
    [|]?\n                       #   optional trailing pipe + newline
)
(?P<rows>               # Data rows:
    ([^\n]*\|[^\n]*     #   Each row must contain at least one pipe
    (\n|$))*            #   Terminated by newline or end-of-string
)
```

The divider uses two alternatives to ensure at least one pipe appears
in the repeating group, preventing catastrophic backtracking. Data
rows require `|` on each line — a line without `|` terminates the
table, preventing the rows pattern from consuming non-table content.

## Sanitization

**Chain (in order):** CodeBlock
**Own sanitize():** Replaces entire match (header + divider + rows)
with whitespace, preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 4.10. Known gaps:

- Escaped pipes (`\|`) in cells cause over-split. `split("|")`
  does not handle backslash escapes.
- CRLF line endings cause complete match failure.

## Notes

- The `extract()` method post-processes the raw match to strip
  leading/trailing pipes and split cells by `|`. Each cell is
  whitespace-stripped.
- The divider regex was rewritten to eliminate catastrophic
  backtracking. The original pattern used an optional pipe `[|]?`
  inside a repeating group followed by a mandatory pipe, causing
  exponential O(2^n) time on long dash sequences without pipes.
  See issue `parser-robustness.md` and hub spec design decisions.
