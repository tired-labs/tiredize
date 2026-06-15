---
assignee:
created: 2026-02-28
knowledge: []
priority: low
status: draft
step:
tags: []
type: bug
workflow: software-engineering
---

# Handle relative URLs without dot prefix in check_url_valid

## Summary

`check_url_valid()` only recognizes relative file paths that start with
`.` (e.g., `./foo.md`, `../bar.md`). A relative URL like `sibling.md`
(no leading dot) falls through to the HTTP validation branch, where
`requests.get()` fails with a `MissingSchema` or `RequestException`.
The function returns `(False, None, "<exception text>")` instead of
resolving the path as a local file.

Discovered during peer review of `fix-relative-url-resolution`.

## Acceptance Criteria

- [ ] Define which URL patterns should be treated as relative file
      paths (e.g., no scheme, no leading `#`, not starting with `.`)
- [ ] Update `check_url_valid()` to resolve these patterns as local
      files against `document.path.parent`
- [ ] Unit tests cover: bare filename (`sibling.md`), subdirectory
      path (`sub/file.md`), and paths that look relative but aren't
      (e.g., `mailto:`, `ftp://`)
- [ ] Linter specification updated to document the full set of
      recognized URL patterns

## Design Decisions

Out of scope: anchor validation (`#` URLs), HTTP/HTTPS URL validation,
and the existing `./` and `../` relative path handling (already fixed).

## Open Questions

- What heuristic should distinguish a bare relative path from other
  non-HTTP URL schemes? Should we check for the presence of `://` or
  maintain an explicit allowlist of recognized schemes?

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Migrated to the v2 issue format during the `.context/` process
    migration. Out of Scope folded into Design Decisions; the v1
    Completion Report was dropped.
