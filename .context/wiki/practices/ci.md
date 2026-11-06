# Continuous Integration

## Overview

What GitHub Actions runs for tiredize. The test rules are on
[testing](./testing.md).

## Workflows

`.github/workflows/ci.yaml` runs on pushes to `main`, on every pull
request and by hand. On Python 3.11 it:

1. installs pytest, pytest-cov, flake8 and coveralls by name;
2. installs tiredize with `pip install -e .`;
3. runs `flake8 tiredize tests`;
4. runs `pytest --cov=tiredize --cov-report=xml`;
5. uploads coverage to Coveralls with `coverallsapp/github-action`,
   which does not fail the build if the upload fails.

`ci.yaml` does not run on tag pushes and publishes nothing.

`.github/workflows/release.yaml` runs on pushes of `v*` tags and by
hand. It runs flake8 and the full test suite on Python 3.12 and, only
if they pass, builds tiredize and publishes it to TestPyPI and, for a
release tag, to PyPI. Its jobs, guards and use are on
[releasing](../operations/releasing.md).

These two are the only workflows. Dependabot is configured in
`.github/dependabot.yml`.

Every action either workflow uses is pinned to a full commit SHA, with
the release it was resolved from in a comment, such as
`actions/checkout@<sha>  # v7.0.1`. To update an action, resolve the
new release's tag to its commit (dereferencing an annotated tag) and
replace both the SHA and the comment.

Dependabot (`.github/dependabot.yml`) proposes those updates: once a
week it opens one pull request for all actions with a release at least
14 days old. Before merging one, read the release notes, above all
for a new major version. CI on the pull request runs only `ci.yaml`,
so after merging an update that touches `release.yaml`, run `Release`
by hand on `main` before the next release.

## Design Decisions

- **Actions are pinned to commit SHAs, not tags.** A tag can be moved
  to new code; a SHA cannot. This matters most in the publish jobs,
  which hold `id-token: write` and so can publish tiredize.
- **Dependabot updates the pins, with a 14-day cooldown,** so the pins
  do not go stale and a bad or compromised release has time to be
  found before it is proposed.
