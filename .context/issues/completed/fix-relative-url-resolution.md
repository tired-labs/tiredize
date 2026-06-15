---
status: done
type: bug
priority: high
created: 2026-02-28
---

# Fix relative URL resolution in check_url_valid

## Summary

`check_url_valid()` in `tiredize/linter/utils.py` resolves relative
URLs (e.g., `./foo.md`) against `document.path` directly. Since
`document.path` is a file path (e.g., `/docs/report.md`), joining
produces `/docs/report.md/foo.md` instead of `/docs/foo.md`. The fix
is to resolve against `document.path.parent`.

## Acceptance Criteria

- [x] `check_url_valid()` resolves relative URLs against
      `document.path.parent` instead of `document.path`
- [x] Unit tests cover: relative URL resolves correctly, relative URL
      file not found, document with no path returns error
- [x] Linter specification updated to say "resolves relative to the
      document's directory (`document.path.parent`)"

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Anchor validation logic (not affected by this bug)
- HTTP URL validation logic (not affected by this bug)
- Adding tests for `check_url_valid` beyond the relative URL path
  (covered by `test-coverage-audit.md`)

## Design Decisions

- Relative URLs without a leading `.` (e.g., `sibling.md`) fall through
  to the HTTP validation path. This is pre-existing behavior and out of
  scope for this fix. Could be addressed in `test-coverage-audit.md`.

## Open Questions

## Completion Report

This issue predates the current issue file format. Completion report
sections will be populated if the issue is revisited.

### Progress

- [x] Implementation complete
- [ ] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [x] User accepted

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
