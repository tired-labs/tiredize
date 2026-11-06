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

# Pin and upgrade every GitHub Action and fix the TestPyPI upload

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
- [x] Every action is at its latest release; the four `actions/*`
      actions move up major versions after their release notes were
      checked for changes affecting these workflows
- [x] The CI wiki page records the pinning rule
- [ ] A manual `Release` run publishes a dev version to TestPyPI and
      passes the install check (user, after merge)

## Design Decisions

- Pin to commit SHAs everywhere, not only in the publish jobs (user,
  2026-11-06).
- Upgrade every action to its latest major in the same change (user,
  2026-11-06). Breaking changes checked and found not to apply:
  checkout v5-v7 (Node 24, credentials file, `pull_request_target`
  fork guard), setup-python v6-v7 (Node 24, `pip-install` input
  removed, unused here), upload-artifact v5-v7 and download-artifact
  v5-v8 (Node 24, by-ID path change and hash-mismatch errors; artifacts
  here are zipped and downloaded by name).
- Done directly by the PM as a mechanical change; SHAs were resolved
  from each tag through the GitHub API, dereferencing annotated tags.

## Open Questions

None.
