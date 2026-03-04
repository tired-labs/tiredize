---
status: draft
type: bug
priority: low
created: 2026-02-28
---

# Handle relative URLs without dot prefix in check_url_valid

## Summary

`check_url_valid()` only recognizes relative file paths that start with
`.` (e.g., `./foo.md`, `../bar.md`). A relative URL like `sibling.md`
(no leading dot) falls through to the HTTP validation branch, where
`requests.get()` fails with a `MissingSchema` or `RequestException`.
The function returns `(False, None, "<exception text>")` instead of
resolving the path as a local file.

Discovered during peer review of `fix-relative-url-resolution.md`.

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

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Anchor validation (`#` URLs)
- HTTP/HTTPS URL validation
- Existing `./` and `../` relative path handling (already fixed)

## Design Decisions

## Open Questions

- What heuristic should distinguish a bare relative path from other
  non-HTTP URL schemes? Should we check for the presence of `://` or
  maintain an explicit allowlist of recognized schemes?

## Completion Report

This issue predates the current issue file format. Completion report
sections will be populated if the issue is revisited.

### Progress

- [ ] Implementation complete
- [ ] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [ ] User accepted

### Problem

### Solution

### Test Summary

### Coverage

### SE Peer Review

#### Incorporated

#### Not Incorporated

### QA Engineer Review

#### Incorporated

#### Not Incorporated

### Technical Architect Review

#### Incorporated

#### Not Incorporated

### Follow-Up Work

### Breaking Changes

### Process Feedback
