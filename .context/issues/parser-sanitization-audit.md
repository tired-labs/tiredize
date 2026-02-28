Status: draft

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
