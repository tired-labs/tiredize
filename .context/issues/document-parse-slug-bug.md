Status: draft

# Fix Document._parse Slug Propagation Bug

## Summary

`Document._parse` updates header slugs via `dataclasses.replace()` but
the replacement creates new objects. Subsection references in the tree
still point to the original pre-replace objects, so slug updates do not
propagate through the document tree.

## Acceptance Criteria

- [ ] Identify all code paths where `dataclasses.replace()` creates
      stale references in the section tree
- [ ] Fix slug propagation so all subsection references reflect the
      updated slug values
- [ ] Add unit tests verifying slug consistency across the document
      tree after parsing

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Refactoring the parser beyond what is needed to fix this bug
- Changes to the Section extraction logic

## Design Decisions

## Open Questions

- Should the fix mutate in place (requires `frozen=False` on Header)
  or rebuild the tree with correct references?
- Are there other fields besides `slug` that suffer from the same
  stale-reference problem?
