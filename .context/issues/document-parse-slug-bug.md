Status: active

# Fix Document._parse Slug Propagation Bug

## Summary

`Document._parse` recalculates header slugs with global dedup context
after `Section.extract()` has already built the section tree (including
subsection references via `_map_subsections`). The recalculation uses
`dataclasses.replace()` which creates new Section and Header objects
and assigns them to `self.sections[i]`, but the `subsections` lists
inside each section still hold references to the original pre-replace
objects. This means subsection slugs are stale after parsing.

## Root Cause

In `document.py` lines 88-89:

```python
new_header = replace(section.header, slug=slug)
self.sections[i] = replace(section, header=new_header)
```

`_map_subsections()` runs on line 78 of `section.py` before this loop,
so subsection references are already wired to the original objects.
Replacing objects in the flat list does not update those references.

## Fix

Both `Header` and `Section` are `frozen=False`, so direct mutation
works. Replace the two `replace()` calls with:

```python
section.header.slug = slug
```

No new objects are created, so subsection references stay valid.
The `replace` import can be removed from `document.py` if no other
call sites remain.

## Acceptance Criteria

- [ ] Replace `dataclasses.replace()` slug update with direct mutation
      on `section.header.slug`
- [ ] Remove unused `replace` import from `document.py`
- [ ] Add test: document with nested headings has consistent slugs
      when accessed via both `doc.sections` and subsection traversal
- [ ] Add test: duplicate heading titles produce correct dedup suffixes
      in both the flat list and subsection tree
- [ ] All existing tests pass

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Refactoring the parser beyond what is needed to fix this bug
- Changes to the Section extraction logic
- Slug dedup strategy changes (title-based vs slug-based)

## Design Decisions

- Mutate in place rather than rebuild tree. Both dataclasses are
  already `frozen=False`. Direct mutation is simpler and avoids
  the stale-reference problem entirely.
- `slug` is the only field recalculated in `_parse()` after tree
  construction, so no other fields suffer from the same problem.

## Open Questions
