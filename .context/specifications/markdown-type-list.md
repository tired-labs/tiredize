# Specification: List

**GFM Equivalent:** Lists (GFM spec sections 5.2, 5.3)
**Source File:** `tiredize/markdown/types/list.py`
**GFM Compliance:** Stub

## Description

List is a placeholder for ordered and unordered list extraction. The
`extract()` method exists but always returns an empty list. No regex
pattern is defined.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `end` | `int` | End position (unused — stub) |
| `items` | `list[str]` | List item strings (unused — stub) |
| `match` | `str` | Raw matched text (unused — stub) |
| `start` | `int` | Start position (unused — stub) |
| `sublists` | `list[List]` | Nested sublists (unused — stub) |

## Regex Pattern

None. No regex pattern is defined.

## Sanitization

**Chain (in order):** (none)
**Own sanitize():** Not implemented. No `sanitize()` method exists.

## GFM Compliance

Stub. The List type has a dataclass definition and a no-op
`extract()` method that returns an empty list for any non-empty
input (returns `[]` for empty input as well). No list parsing is
implemented.

GFM defines two list types:
- Bullet lists (section 5.2): lines beginning with `-`, `*`, or `+`
- Ordered lists (section 5.3): lines beginning with a number and
  `.` or `)`

Neither is supported.

## Notes

- The `extract()` method accepts `text` and `base_offset` parameters
  consistent with the element type pattern, but the `base_offset` is
  unused.
- The dataclass does not follow the standard element type pattern:
  it uses `start`/`end` integers instead of a `Position` field, and
  `match` instead of `string`.
- `List.extract()` is still called by `Section._extract()` —
  it simply contributes an empty list to every section.
