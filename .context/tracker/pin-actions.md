---
assignee:
created: 2026-11-06
knowledge: []
priority: high
status: in-progress
step:
tags: []
type: bug
workflow: to-be-determined
---

# Pin every GitHub Action to a commit and fix the TestPyPI upload

## Summary

The first manual `Release` run failed at the TestPyPI upload:
`pypa/gh-action-pypi-publish@v1.13.0` bundles a twine that rejects
core metadata 2.5, which hatchling 1.33.0 now writes ("'2.5' is not a
valid metadata version"). Nothing was uploaded. Support for 2.5 came
in v1.14.2; v1.14.3 also fixes security advisory GHSA-5xjx-3w67-w9x9.

At the same time, pin every action in both workflows to a full commit
SHA instead of a movable tag, so a compromised or moved tag cannot run
new code, above all in the publish jobs that hold `id-token: write`.

This issue updates these wiki pages and files:

- [CI](../wiki/practices/ci.md)
- [releasing](../wiki/operations/releasing.md)

## Acceptance Criteria

- [x] Both publish steps use `pypa/gh-action-pypi-publish` v1.14.3
- [x] Every `uses:` in `.github/workflows/` names a full 40-character
      commit SHA, with the release it was resolved from in a comment
- [x] Each other action stays on its current major version, at that
      major's latest release
- [x] The CI wiki page records the pinning rule
- [ ] A manual `Release` run publishes a dev version to TestPyPI and
      passes the install check (user, after merge)

## Design Decisions

- Pin to commit SHAs everywhere, not only in the publish jobs (user,
  2026-11-06).
- Done directly by the PM as a mechanical change; SHAs were resolved
  from each tag through the GitHub API, dereferencing annotated tags.

## Open Questions

None.
