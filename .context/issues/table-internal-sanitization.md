Status: ready

# Add internal CodeBlock sanitization to Table.extract()

## Summary

`Table.extract()` is the only extractor that does not sanitize
internally. It relies on `Section._extract()` to pass
`CodeBlock.sanitize(string)` as input. This violates the design
principle established in `parser-sanitization-gaps.md`: each
extractor should be self-contained and produce correct results
regardless of calling context.

The external sanitization was originally added as a defense against
a catastrophic backtracking vulnerability in the table regex
(`parser-robustness.md`). That vulnerability has since been fixed
by rewriting the regex, so the external sanitization is now
belt-and-suspenders rather than the primary fix. Table should
sanitize internally like every other extractor.

## Acceptance Criteria

- [ ] `Table.extract()` calls `CodeBlock.sanitize()` on the input
      text before matching
- [ ] `Section._extract()` can pass raw `string` to `Table.extract()`
      instead of `CodeBlock.sanitize(string)` (since Table now
      handles it internally)
- [ ] All existing tests pass (no regressions)
- [ ] Parser specification updated: sanitization chain table changed
      from "(none, but Section._extract passes CodeBlock-sanitized
      text)" to "CodeBlock"
- [ ] Parser specification "Section._extract() Orchestration"
      section updated to reflect that all extractors now receive
      raw `string` (remove the Table exception note)

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Table regex changes
- Additional sanitization (e.g., CodeInline) for Table
- Changes to the `string_safe` field or its consumers

## Design Decisions

- **Table sanitizes CodeBlock internally, matching all other
  extractors.** The backtracking vulnerability that motivated the
  external sanitization is already fixed. Internal sanitization makes
  Table safe to call from any context.

## Open Questions
