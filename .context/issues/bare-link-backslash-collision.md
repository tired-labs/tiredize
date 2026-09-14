---
assignee:
created: 2026-09-14
knowledge: []
priority: medium
status: ready
step:
tags: [parser, pr-44]
type: bug
workflow: software-engineering
---

# BareLink Backslash Matching Collides with GFM Escape Syntax

## Summary

`BareLink.RE_URL` treats a backslash as the start of a Windows-style
file path. GFM treats a backslash as an escape character. In running
prose these are indistinguishable, so any escaped punctuation preceded
by whitespace is extracted as a bare link and handed to the `links`
rule for validation, where it is reported as unreachable.

On current `main`:

```
Matches \*.dll in the target directory.            ->  ['\*.dll']
Drops a payload at \Windows\System32\cmd.exe ...   ->  ['\Windows\System32\cmd.exe']
Escape pipes as \| inside table cells.             ->  ['\|']
Beacons to \\attacker\share over SMB.              ->  ['\\attacker\share']
Uses the \_hidden\_ registry value.                ->  ['\_hidden\_']
```

None of these are links. All five produce findings and a non-zero exit
status on a document with nothing wrong with it.

The decisive point is that the backslash branch cannot produce a true
positive. `check_url_valid()` resolves only paths beginning with `.` as
local files; everything else goes to the HTTP branch, where a backslash
path fails with `MissingSchema`. There is no input for which a matched
backslash path validates successfully. Every match is a finding and
every finding is noise.

This is not a GFM parity gap. `BareLink` is a deliberate superset of
GFM — GFM autolinks only `http://`, `https://`, `www.`, and email, and
never autolinks relative paths at all. The bug lives in the
tiredize-specific extension, which is why splitting `gfm-parity` by
element type does not produce a home for it.

The collision has been patched once already: `RE_URL` only matches a
backslash at the start of a line or after whitespace, `[`, or `(`,
which is why `HKLM\SYSTEM\CurrentControlSet` is correctly skipped. That
guard was added for the same class of complaint. It does not help,
because a markdown escape almost always follows a space.

## Acceptance Criteria

- [ ] The `\\` alternative is removed from `BareLink.RE_URL` in
      `tiredize/markdown/types/link.py`
- [ ] `./` and `../` relative path extraction is unchanged
- [ ] `test_bare_link_backslash` is inverted to assert no match, and
      renamed to reflect that backslash paths are not bare links
- [ ] `test_bare_link_backslash_not_matched_mid_word` retained, with its
      docstring updated — its original rationale (a mid-word guard on a
      supported backslash branch) no longer applies
- [ ] Regression tests added covering the escape cases: `\*.dll`, `\|`,
      `\_x\_.md`, `\\server\share`, and an escaped sequence that ends in
      a file extension
- [ ] `.context/specifications/markdown-parser.md` — the sentence
      "Backslash paths (`\`) are also supported for Windows-style paths"
      removed from the BareLink Relative Path Matching section
- [ ] `.context/specifications/markdown-parser.md` — the Pattern
      Reference block for `BareLink.RE_URL` updated; it is already stale
      and shows a superseded form with `\S+`
- [ ] Full test suite passes

## Design Decisions

- Remove the branch rather than narrow it. Narrowing is a heuristic over
  a genuine ambiguity and leaks: requiring a file extension still admits
  `\_my\_file.md`, and silently drops extensionless paths such as
  `\docs\readme`.
- `BareLink` remains a deliberate superset of GFM after this change.
  `./` and `../` extraction is retained because validating relative
  documentation links is the rule's purpose. This issue removes a
  collision with GFM syntax; it does not make `BareLink` GFM-conformant,
  and the issue text should not be read as licence to remove relative
  path support.
- Out of scope: the two genuine GFM gaps in `BareLink` — `www.`
  autolinks and email autolinks — both currently skipped tests. Those
  belong to `gfm-parity`.
- Out of scope: validating Windows paths. If that is ever wanted it is a
  real feature needing a real design (resolution against the document
  directory, as `./` already does), not a regex branch that can only
  emit errors.

## Open Questions

## Comments

### 2026-09-14T00:00:00+00:00

Author: program-manager

    Surfaced during triage of PR #44, which proposed narrowing the
    regex rather than removing the branch. That fix was verified
    incomplete: `\_my\_file.md` and `\_x\_.json` still false-positive
    under it, and extensionless backslash paths became silently
    undetected.

    The removal was verified in a throwaway worktree before this issue
    was written. Deleting `|\\` from the pattern clears all five prose
    cases above, leaves `./appendix.md` extraction intact, and produces
    exactly one test failure — `test_bare_link_backslash`, the test
    asserting the behaviour being removed. 843 passed, 1 failed, 50
    skipped.
