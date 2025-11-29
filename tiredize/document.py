# from __future__ import annotations
# from dataclasses import dataclass
# from pathlib import Path
# from typing import List, Dict, Optional, Tuple
# import re
# import yaml

# def _split_table_row(line: str) -> List[str]:
#     """
#     Split a markdown table row into cell texts.

#     Keeps empty cells intact, strips outer pipes and whitespace.
#     """
#     # Remove leading/trailing pipe if present
#     s = line.rstrip()
#     if s.startswith("|"):
#         s = s[1:]
#     if s.endswith("|"):
#         s = s[:-1]

#     cells: List[str] = []
#     cell = ""
#     escaped = False

#     # Parse the row character by character to handle escaped pipes
#     for i in s:

#         # Handle unescaped pipe as cell separator
#         if (not escaped) and (i == "|"):
#             cells.append(cell.strip())
#             cell = ""
#             continue

#         # Otherwise, add character to current cell
#         cell += i

#         # Handle escape character
#         if i == "\\":
#             escaped = True
#             continue

#         # Reset escape state
#         escaped = False

#     # Add the last cell
#     cells.append(cell.strip())
#     return cells


# def _extract_tables(text: str, fenced_lines: set[int]) -> List[Table]:
#     """
#     Extract simple GitHub style markdown tables.

#     Tables are contiguous blocks of lines that match RE_TABLE_ROW,
#     excluding any lines inside fenced code blocks.
#     """

#     tables: List[Table] = []
#     lines = text.splitlines()
#     i = 0

#     while i < len(lines):
#         line_no = i + 1

#         # Skip lines that are inside fenced code or not table rows
#         if line_no in fenced_lines or not RE_TABLE_ROW.match(lines[i]):
#             i += 1
#             continue

#         # Start collecting a table
#         block: List[Tuple[int, str]] = []

#         # Collect a contiguous block of table lines, all outside fenced code
#         while i < len(lines):
#             line_no = i + 1

#             # Stop if we hit fenced code or a non-table row
#             if line_no in fenced_lines or not RE_TABLE_ROW.match(lines[i]):
#                 break

#             # Ignore tables without a divider as second row
#             if len(block) == 1 and not RE_TABLE_DIV.match(lines[i]):
#                 break

#             # Add this line to the current table block
#             block.append((line_no, lines[i]))
#             i += 1

#         # Ignore tables that are too short to be valid
#         if len(block) < 2:
#             continue

#         # Parse the header row
#         header_line_no, header_line = block[0]
#         header = _split_table_row(header_line)

#         # Parse the body rows that come after the divider row
#         body_rows: List[List[str]] = []
#         data_block = block[2:]

#         # Parse each data row
#         for _, row_text in data_block:
#             body_rows.append(_split_table_row(row_text))

#         # Store the parsed table
#         tables.append(
#             Table(
#                 header=header,
#                 rows=body_rows,
#                 start_line=header_line_no,
#                 end_line=block[-1][0],
#             )
#         )

#     return tables


# def _extract_links_and_images(text: str, fenced_lines: set[int])
# -> List[Link]:
#
#     """
#     Extract URLs from the document body, skipping fenced code.

#     For now, global link detection is simple:
#       a line is considered a global link definition if it looks like:
#         [label]: url
#       or a reference style variant.
#     """
#     links: List[Link] = []
#     lines = text.splitlines()

#     for i, line in enumerate(lines, start=1):

#         # Skip lines inside fenced code
#         if i in fenced_lines:
#             continue

#         # Remove inline code spans to avoid false positives
#         search_line = RE_CODE_INLINE.sub("", line)

#         for m in RE_LINK_INLINE.findall(search_line):
#             if m[0] == "!":
#                 # TODO: Store images as well
#                 # print(f"IMAGE: [{m[1]}] ------------ {m[2]} at line {i}")
#                 continue
#             else:
#                 links.append(
#                     Link(
#                         is_inline=True,
#                         is_reference=False,
#                         url=m[2].strip(),
#                         title=m[1].strip(),
#                         line=i,
#                     )
#                 )

#         for m in RE_LINK_REFERENCE.findall(search_line):
#             links.append(
#                 Link(
#                     is_inline=False,
#                     is_reference=True,
#                     url=m[1].strip(),
#                     title=m[0].strip(),
#                     line=i,
#                 )
#             )

#     return links
