---
status: draft
type: spike
priority: medium
created: 2026-02-28
---

# Parser Sanitization and Regex Safety Audit

## Summary

Audit all markdown parser extractors for sanitization gaps and regex
backtracking vulnerabilities. The table extractor was fixed (see
`parser-robustness.md`), but the remaining extractors have not been
systematically audited.

## Acceptance Criteria

- [ ] Write unit tests validating the sanitize chain precedence order
      against GitHub-Flavored Markdown rendering rules
- [ ] Audit all extractors in `Section._extract()` for sanitization
      gaps -- determine which extractors need pre-sanitized input to
      avoid false matches inside code blocks
- [ ] Stress test all `RE_*` regex patterns in `markdown/types/`
      against adversarial input (long strings, deeply nested
      constructs, repeated special characters) with time thresholds
- [ ] Fix any backtracking vulnerabilities or false-match bugs found

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Linter rule changes
- Schema validator changes
- New markdown element types

## Design Decisions

## Open Questions

- What time threshold constitutes a backtracking vulnerability? (e.g.,
  >1 second for a 10,000-character input?)
- Should extractors that do their own internal sanitization (link
  types) be refactored to use the centralized sanitize chain, or is
  the current approach acceptable?

## References

- Sanitize chain current state: `specifications/markdown-parser.md`
- Prior fix: `parser-robustness.md`

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
