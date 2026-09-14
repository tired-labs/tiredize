---
assignee:
created: 2026-09-14
knowledge: []
priority: high
status: draft
step:
tags: [pr-44, schema-validator]
type: refactor
workflow: software-engineering
---

# Rework Markdown Schema Finding Taxonomy and Locations

## Summary

The markdown schema validator reports findings that are hard to act on.
Three problems, coupled closely enough that fixing them separately would
mean rewriting the same messages twice.

### Missing sections have no location

All three `missing_section` construction sites in
`tiredize/validators/markdown_schema.py` hardcode
`Position(offset=0, length=0)`, so every missing section is reported at
the first character of the document regardless of where it belongs.
Against the project's own issue schema:

```
sparse.md:1:0: [schema.markdown.missing_section] Missing required section: 'Acceptance Criteria'
sparse.md:1:0: [schema.markdown.missing_section] Missing required section: 'Design Decisions'
sparse.md:1:0: [schema.markdown.missing_section] Missing required section: 'Open Questions'
```

Three findings, one position. An editor jumping to any of them lands on
the title. This is a bug, not a wording problem.

### Messages omit the heading level

`missing_section` and `unexpected_section` name a section but not its
level, which is half of what identifies it. `wrong_level` already gets
this right (`is level 3, expected 2`), so the format exists in the
codebase and is not being applied consistently.

### `wrong_level` treats a section as its name alone

A section is the pairing of a name and a heading level. A level-3
"Details" is not the level-2 "Details" at the wrong depth; it is a
different section that happens to share a string. `wrong_level` encodes
the opposite assumption, matching on name and then reporting the level
as a discrepancy, which is the validator inventing a fuzzy match the
schema never asked for.

Under name-and-level identity the case resolves into the two existing
presence findings: the expected section was not found, and a section the
schema does not define was.

## Acceptance Criteria

- [ ] `missing_section` reports a position that locates where the
      section was expected, rather than `Position(offset=0, length=0)`
      (3 construction sites)
- [ ] `missing_section` messages carry the expected heading level
- [ ] `unexpected_section` messages carry the heading level of the
      offending section (4 construction sites)
- [ ] `schema.markdown.wrong_level` is removed (4 construction sites);
      the cases it covered are reported as `missing_section` plus
      `unexpected_section`
- [ ] Where an unexpected section's name matches a schema entry at a
      different level, the message says so, without that near-miss
      affecting how the finding is classified. For example:
      `Unexpected section 'Alpha' (level 3); schema defines 'Alpha' at
      level 2`
- [ ] `schema.markdown.out_of_order` is retained unchanged in scope
- [ ] Error Types table in
      `.context/specifications/markdown-schema-validator.md` updated
- [ ] README rule ID documentation updated
- [ ] Tests covering `wrong_level` migrated to assert the new pairing
      (9 references in `tests/validators/test_markdown_schema.py`)
- [ ] The repository's own schemas still validate every file in
      `.context/issues/` cleanly

## Design Decisions

- **A section is the pairing of its name and its heading level.**
  Neither identifies a section alone. The schema already declares both
  on every entry; the validator should not treat them as separable, nor
  guess that a heading at the wrong depth "meant" an entry elsewhere.
  This is what collapses `wrong_level` into the two presence findings.

- **`out_of_order` is retained and is not collapsed.** Level is a
  property of a section; order is a property of the sequence containing
  it. When a section appears in the wrong position its name and level
  still match a schema entry exactly, so nothing about the section is
  unexpected. The container is what is wrong. Ordering is also the only
  finding governed by its own switch: with `enforce_order: false` it
  cannot occur, while the others still can. Folding it into
  `unexpected_section` would make the same document report differently
  based on a toggle unrelated to whether the schema recognises those
  sections. Collapsing it would also turn a single transposition into
  several findings the reader has to reassemble.

- **Near-miss information stays in the message, not the taxonomy.**
  Reporting that an unexpected 'Alpha' at level 3 resembles a schema
  entry for 'Alpha' at level 2 is useful to an author, but it must not
  create a third classification or reintroduce name-only matching in the
  validation logic.

- **The schema language stays explicit.** A schema states exactly what a
  document may contain. Mechanisms that mean "stop checking below this
  point" are out of scope, however convenient, because a schema using
  one no longer describes the document and requires tiredize-specific
  vocabulary to interpret. This is why the `allow_subsections` key
  proposed in PR #44 was declined. The principle should be lifted into
  `markdown-schema-validator.md` under design boundaries at the
  technical reference step, so it outlives this issue.

- Removing a rule ID is a breaking change for anyone matching on
  `schema.markdown.wrong_level`. It is documented in the README and the
  specification, so the change must be reflected in both.

## Open Questions

- What position should `missing_section` report? The parent section's
  header locates the container and works in both ordered and unordered
  mode. The end of the preceding matched sibling reads more naturally in
  ordered mode but has no meaning when order is not enforced. A unified
  rule would be: the preceding matched sibling where one exists,
  otherwise the parent's header. This needs deciding before
  implementation.
- Should `out_of_order` also say where the section was expected, rather
  than only that it is misplaced? Adjacent to this work and cheap while
  the surrounding code is open, but not required by it.

## Comments

### 2026-09-14T00:00:00+00:00

Author: program-manager

    Surfaced while reviewing PR #44. The contributor reported that
    stopping a catch-all pattern one level short produces a misleading
    `unexpected_section`, which is accurate: the finding is correct, but
    the message gives the author no way to tell whether the document or
    the schema is at fault. Investigating that turned up the hardcoded
    position bug, which is the more serious of the two and unrelated to
    their report.

    The taxonomy change came out of the same conversation. The
    name-and-level identity model was the maintainer's; it resolves a
    disagreement about whether `wrong_level` was describing a
    misplaced section or a different one.
