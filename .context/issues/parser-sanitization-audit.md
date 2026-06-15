---
assignee:
created: 2026-02-28
knowledge: []
priority: medium
status: draft
step:
tags: []
type: spike
workflow: software-engineering
---

# Parser Sanitization and Regex Safety Audit

## Summary

Audit all markdown parser extractors for sanitization gaps and regex
backtracking vulnerabilities. The table extractor was fixed (see
`parser-robustness`), but the remaining extractors have not been
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

## Design Decisions

Out of scope: linter rule changes, schema validator changes, and new
markdown element types.

References: sanitize chain current state in
`specifications/markdown-parser.md`; prior fix in `parser-robustness`.

## Open Questions

- What time threshold constitutes a backtracking vulnerability? (e.g.,
  >1 second for a 10,000-character input?)
- Should extractors that do their own internal sanitization (link
  types) be refactored to use the centralized sanitize chain, or is
  the current approach acceptable?

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Migrated to the v2 issue format during the `.context/` process
    migration. Out of Scope and References folded into Design Decisions;
    the v1 Completion Report was dropped.
