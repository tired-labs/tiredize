# Releasing

## Overview

How a version of tiredize is built and published. Releases go to
TestPyPI; nothing publishes to the production PyPI.

## Steps

1. Set `version` in `pyproject.toml`.
2. Push a tag starting with `v` (for example `v0.0.3`), or run the
   `Publish to TestPyPI` workflow by hand.
3. `.github/workflows/release-testpypi.yml` installs tiredize, runs the
   tests, builds the sdist and wheel with `python -m build`, and
   uploads them to TestPyPI with `pypa/gh-action-pypi-publish`, using
   an API token stored as a GitHub Actions secret.

The workflow does not check that the tag matches `version`.

## Design Decisions

None recorded yet.
