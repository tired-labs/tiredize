Status: completed

# Table.extract() IndexError on whitespace-only header match

## Summary

`RE_TABLE` can match a whitespace-only line as the header group. When
this happens, `header.strip()` returns an empty string and the
subsequent `header[-1]` / `header[0]` indexing raises `IndexError`.

This is reachable in practice when `CodeBlock.sanitize()` replaces a
code fence delimiter (e.g., `` ``` ``) with spaces. The resulting
whitespace line satisfies the header pattern `[^\n|]+`, and if a
valid divider line follows (e.g., `|---|`), the regex produces a
match with an empty header.

**Reproduction:**

```python
from tiredize.markdown.types.table import Table

text = "```\nsome code\n```\n|---|\n|1|\n"
Table.extract(text)  # raises IndexError
```

This bug is pre-existing — it was reachable through the
`Section._extract()` path before `table-internal-sanitization.md`
moved sanitization into `Table.extract()`. The same sanitized text
was always passed to the table regex.

**Discovered by:** GitHub Copilot peer review of
`table-internal-sanitization.md`.

## Acceptance Criteria

- [x] `Table.extract()` does not raise `IndexError` on
      whitespace-only header matches
- [x] `RE_TABLE` header pattern requires at least one `|` character
- [x] Parser specification updated if regex is changed
- [x] Regression test added for the reproduction case above

## Out of Scope

- Other table regex changes not related to this bug
- Changes to divider or row parsing logic

## Design Decisions

- Primary fix in the regex: changed the header cell group from
  zero-or-more to one-or-more, requiring at least one pipe. A GFM
  table header must contain a pipe, so a pipeless match is
  semantically invalid. Peer review revealed a second crash path
  where pipe-only headers (e.g., ` | `) become empty after stripping
  outer pipes, so defensive empty-header guards were added in
  `Table.extract()` to skip these degenerate matches.
- The `+` quantifier change also rejects trailing-pipe-only
  single-column headers without a leading pipe (e.g., `Col |`). This
  is technically valid GFM but was never tested and is uncommon in
  practice. Accepted as a minor coverage regression — addressing it
  would require additional regex complexity beyond this fix's scope.

## Open Questions
