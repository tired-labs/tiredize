Status: active

# GFM Compliance Audit and Spec Restructuring

## Summary

The markdown parser specification (`markdown-parser.md`) documents all
element types in a flat structure with regex patterns in one section and
sanitization in another. There is no per-type compliance assessment
against GFM, no clear mapping between internal and GFM naming, and no
documentation of unimplemented GFM features.

This issue restructures the spec into per-type files with a consistent
template, creates a compliance audit against GFM for each type, and
produces sub-issues for unimplemented GFM features.

## Acceptance Criteria

- [x] 16 per-type spec files created following the standard template
- [x] `markdown-parser.md` restructured as a hub document with shared
      concepts only (no per-type regex or sanitization content)
- [x] Every per-type spec includes a GFM compliance assessment
- [x] 8 draft sub-issues created for unimplemented GFM features
- [x] `gfm-parity.md` updated with `Sub-issues:` list
- [x] All per-type specs cross-referenced against source code for
      accuracy
- [x] Linter and tests still pass (no code changes in this issue)

## Out of Scope

- No code changes
- No test changes
- No changes to existing issues beyond `gfm-parity.md` parent update
- No implementation of any GFM features

## Design Decisions

- Per-type spec naming convention: `markdown-type-<name>.md` where
  `<name>` is the lowercase internal type name.
- The hub `markdown-parser.md` retains only cross-cutting content:
  overview, contracts, shared types, utility functions, shared regex
  concepts, file layout, sanitization architecture, and cross-cutting
  design decisions.
- Per-type design decisions move from the hub to their respective type
  specs.
- GFM compliance status uses four levels: Compliant, Partial, Stub,
  Not Implemented.

## Open Questions
