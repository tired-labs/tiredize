---
assignee: ghostwriter
created: 2026-11-06
knowledge: []
priority: high
status: in-progress
step: user-documentation
tags: []
type: feature
workflow: software-engineering
---

# Version tiredize from git tags and publish it to PyPI

## Summary

Publish tiredize to the production PyPI, which a coworker has asked
for, and lock down how versions are numbered first so what is published
is never in doubt. Today the version is typed into `pyproject.toml`
(`0.0.3`), releases go only to TestPyPI through
`release-testpypi.yml` using an API token, and the README's
`pip install tiredize` does not work.

The target: the version comes only from git tags through hatch-vcs,
`tiredize --version` reports it, and a new `release.yaml` tests,
builds, and publishes through Trusted Publishing, to TestPyPI first and
then to PyPI after the user approves. Both registries were reset on
2026-11-06 and nothing named `tiredize` is published on either.

Part of the work is done by the user outside the repository (tag
deletion, environment protection, the secret, the first tag); the rest
is the build configuration, the CLI flag, the release workflow and the
documentation.

This issue updates these wiki pages and files:

- [releasing](../wiki/operations/releasing.md)
- [installing and running](../wiki/operations/installing-and-running.md)
- [CI](../wiki/practices/ci.md)
- [CLI](../wiki/components/cli.md)
- [README](../../README.md)

## Acceptance Criteria

Versioning:

- [x] The version is derived from git tags by hatch-vcs with
      `local_scheme = "no-local-version"`; no file in the repository
      holds a version number
- [x] A build of a commit tagged `vX.Y.Z` has version `X.Y.Z`; a build
      of any other commit has a dev version that sorts after the last
      tag
- [x] `tiredize --version` prints the installed version, read with
      `importlib.metadata`
- [x] The `v0.1` tag is deleted from `origin` and locally (user)
- [x] `authors` in `pyproject.toml` names `TIRED Labs`, with no email

Release workflow (`.github/workflows/release.yaml`):

- [x] `release.yaml` replaces `release-testpypi.yml`, which is deleted;
      `ci.yaml` is unchanged
- [x] Lint and the full test suite run first; nothing is built or
      published unless they pass
- [x] Checkout uses `fetch-depth: 0` so hatch-vcs sees the tags
- [x] The sdist and wheel are built once, pass a metadata check, and
      the wheel installed into a clean environment runs
      `tiredize --version`; the publish jobs receive these files as an
      artifact
- [x] A manual run publishes a dev version to TestPyPI only, through
      the `testpypi` environment
- [x] A tag push publishes to TestPyPI, skipping a version already
      there so a re-run can reach PyPI
- [x] After the TestPyPI publish, the workflow installs that exact
      version from TestPyPI into a clean environment, taking its
      dependencies from pypi.org only, and checks that
      `tiredize --version` prints it
- [x] A tag push publishes to PyPI through the `pypi` environment only
      after the TestPyPI install check passes, the tag is strictly
      `vX.Y.Z`, and the tagged commit is on `main`
- [x] A tag matching `v*` but not `vX.Y.Z` fails before anything is
      built
- [x] Publishing uses Trusted Publishing through
      `pypa/gh-action-pypi-publish`, with `id-token: write` only on the
      publish jobs and no tokens or secrets, matching the registered
      publishers (owner `tired-labs`, repository `tiredize`, workflow
      `release.yaml`, environments `pypi` and `testpypi`)

Outside the repository (user):

- [x] The `pypi` environment requires the user's approval
- [x] The `TEST_PYPI_API_TOKEN` GitHub secret is deleted
- [ ] Tag `v0.1.0` publishes to both registries and
      `pip install tiredize` in a clean environment installs `0.1.0`
      from pypi.org

Documentation:

- [ ] The wiki pages listed in the Summary explain the versioning
      scheme, the release flow, and everything a developer needs to
      cut a release; the README's installation section is accurate

## Design Decisions

- Releases publish through Trusted Publishing (GitHub OIDC); no
  long-lived token or password is stored (user, 2026-11-06).
- Versions come only from git tags through hatch-vcs; tags take the
  form `vX.Y.Z` and follow semantic versioning, chosen by hand when
  tagging, with no automated bumping or release tooling (user,
  2026-11-06).
- The first release is `0.1.0`. Existing tags are deleted to start
  fresh (user, 2026-11-06).
- `--version` ships in `0.1.0`, so every published release can report
  what it is (user, 2026-11-06).
- Tags go through TestPyPI, an install check, and the user's approval
  before PyPI; manual runs are TestPyPI practice runs (user,
  2026-11-06).
- The workflow file is named exactly `release.yaml`, as registered
  with both registries (user, 2026-11-06).
- Both projects are owned by the personal `daemorgue` account until
  the `tired-labs` organizations are approved; the transfer is the
  `pypi-org-transfer` backlog entry (user, 2026-11-06).
- The wiki documents the approach fully; there is no separate release
  procedure file (user, 2026-11-06).
- The package author is `TIRED Labs` with no email; users reach the
  project through GitHub issues (user, 2026-11-06).

- Acceptance tests are kept in the suite only for behavior that can
  regress: `--version`, and an offline check that `pyproject.toml`
  takes the version from git with `no-local-version` and holds none
  itself. Every other criterion, including the release workflow's
  structure, the author and the deleted file, is a one-time check
  that Acceptance Verification records with evidence, with no
  committed test. No test builds wheels or needs network access
  (user, 2026-11-06).

## Open Questions

None.
