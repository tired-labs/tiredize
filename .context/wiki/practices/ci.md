# Continuous Integration

## Overview

What GitHub Actions runs for tiredize. Releasing is on
[releasing](../operations/releasing.md); the test rules are on
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

The release workflow runs the tests again on Python 3.12 before it
publishes.

## Design Decisions

None recorded yet.
