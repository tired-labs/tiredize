Status: draft

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

- [ ] `Table.extract()` does not raise `IndexError` on
      whitespace-only header matches
- [ ] `RE_TABLE` header pattern requires at least one `|` character,
      or matches with empty stripped headers are skipped before
      indexing
- [ ] Parser specification updated if regex is changed
- [ ] Regression test added for the reproduction case above

## Out of Scope

- Other table regex changes not related to this bug
- Changes to divider or row parsing logic

## Design Decisions

## Open Questions

- Should the fix be in the regex (tighten the header pattern to
  require a pipe) or in the extraction logic (skip matches where
  the header is empty after stripping)? A regex fix prevents the
  match entirely; a logic fix is more defensive but leaves a
  semantically invalid match in the regex.
