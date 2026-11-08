# Testing

## Overview

How tiredize is tested and what a change must keep passing. Where test
files live is on [repository layout](../repository/layout.md); what CI
runs is on [CI](./ci.md).

## Running

uv is required. From the repository root, run once and again after
`uv.lock` changes:

```bash
uv sync
```

It creates `.venv` (ignored by git) and installs tiredize in editable
mode with the `dev` group at the versions in `uv.lock`, so a local
environment matches CI. The groups and the lock are on
[CI](./ci.md#locked-dependencies). Run the same checks as CI through uv,
or activate `.venv` and run them directly:

```bash
uv run flake8 tiredize tests
uv run pytest --cov=tiredize
```

Unlike CI, `uv sync` builds tiredize with build isolation, so hatchling
and hatch-vcs are fetched for that build rather than taken from the
lock.

The entry-point tests in `tests/test_main_module.py` run the installed
`tiredize` console script. They are meaningful only when that script is
an editable install of the working tree; a stale copy on `PATH` is not
detected, and an absent one is skipped.

## Rules

- **Tests assert the specified behaviour,** not whatever the code does
  today. Where the wiki or GFM says one thing and the code does another,
  the test asserts the specified result.
- **A known defect is a skipped test, not a missing one.** The test is
  written, seen to fail, then marked
  `@pytest.mark.skip(reason="<slug>: …")`, where `<slug>` names the
  backlog entry or issue that will fix it. The fix removes the skip. GFM
  gaps in the parser use the slug `gfm-parity`. `pytest -rs` lists every
  skip and its reason; counts are taken from it, not from documents.
- **GFM examples are pinned by number.** Where the parser claims GFM
  parity, each specification example has one test that names its number
  and asserts the extracted `string` and `url`, not HTML
  (`tests/markdown/types/test_link_gfm_autolinks.py`).
- **No network.** HTTP is mocked with `unittest.mock`, patching
  `requests.get` in the `check_url_valid` tests. The `links` rule tests
  mock `check_url_valid` itself, so they test the rule's branching only.
- **Packaging is checked statically.** `tests/test_versioning.py` reads
  `pyproject.toml` and the tracked files: the version comes from git
  through hatch-vcs with `no-local-version`, and no file holds a version
  number. It skips on Python 3.10, which lacks `tomllib`. No test builds
  a distribution, installs one or runs a workflow; the release workflow
  checks the built and published package itself (see
  [releasing](../operations/releasing.md)).
- **Coverage aims at 100%.** A line is excluded only when it is
  unreachable, with the reason written in the test file. The target is
  not enforced: CI sets no threshold.
- **`__main__.py` is covered in-process** with `runpy.run_module` and a
  patched `sys.argv`, not by subprocess coverage, which needs extra
  machinery and tends to be flaky.
- **The tooling contract is tested statically.** `tests/test_tooling.py`
  reads `pyproject.toml`, `uv.lock`, `dependabot.yml` and the workflows:
  the groups and their minimums, the pins and hashes in the lock, and
  that the workflows install only from the lock. It reads `run:` steps
  heuristically; installing only from the lock is the supply-chain
  invariant, so these stay regression tests. A real run is the check
  for what a test cannot see: the build tool versions in the `Release`
  log and the first Dependabot `uv` pull request.
- **Real documents are checked by hand.** Changes to the parser or the
  schema validator are also run against the TRRs in the techniques
  repository; that is how the table backtracking hang was found.

## Design Decisions

- **Skipped tests as the record of known gaps,** so the gap and its
  fix are tied to a test and a slug rather than to prose that drifts.
- **Pinned specification examples are the record of GFM parity,**
  instead of a copy of the specification kept in the repository.
- **Release behaviour is tested only where it can regress.** The suite
  keeps tests for `--version` and for where the version comes from;
  the release workflow's structure is checked when it is changed, not by
  a committed test, because a test of it would need builds or network
  access.
