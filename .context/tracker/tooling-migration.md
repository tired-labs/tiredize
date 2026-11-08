---
assignee: qa-engineer
created: 2026-11-06
knowledge: []
priority: high
status: in-progress
step: acceptance-verification
tags: []
type: refactor
workflow: software-engineering
---

# Hash-lock CI and release tools and keep them current with Dependabot

## Summary

The Actions in `ci.yaml` and `release.yaml` are pinned to commit SHAs,
but the packages their steps install with pip are not: pip, build,
twine, flake8, pytest, pytest-cov and the build backend (hatchling,
hatch-vcs) are named without versions, and their nested dependencies
float too, about 48 packages in all. Each run gets whatever is newest.
An unpinned hatchling 1.33.0 is what broke the first TestPyPI upload,
and any tampered release reaches CI the same way.

Declare the development and release tools as dependency groups in
`pyproject.toml`, lock every package with uv in `uv.lock`, install
every package both workflows use from that lock with hashes checked,
and have Dependabot propose updates to the lock. Drop the `twine check`
step, which the publish Action already does. Replace the Coveralls
Action, which downloads an unlocked reporter program at run time, with
the `coveralls` package from the lock. Also finish the import-grouping
comments in the test files that lack them.

This issue updates these wiki pages:

- [CI](../wiki/practices/ci.md)
- [testing](../wiki/practices/testing.md)
- [releasing](../wiki/operations/releasing.md)

## Acceptance Criteria

- [ ] `pyproject.toml` has a `[dependency-groups]` table with a `dev`
      group (flake8, pytest, pytest-cov) and a `release` group (build,
      hatchling, hatch-vcs), each with minimum versions only
- [ ] A committed `uv.lock` pins an exact version and sha256 hashes for
      every package the workflows install, nested dependencies and
      `PyYAML` and `requests` included
- [ ] Every step in `ci.yaml` and `release.yaml` that installs packages,
      the wheel check and the TestPyPI install check included, installs
      them from `uv.lock` with hashes checked, and installs only the
      groups that job uses
- [ ] No step installs a package that is not in `uv.lock`, including
      the build tools `pip install -e .` and `python -m build` would
      otherwise fetch into an isolated environment
- [ ] `python -m build` in `release.yaml` builds with the locked
      hatchling and hatch-vcs, shown by the versions in a run's log
- [ ] uv is installed in CI by `astral-sh/setup-uv`, pinned to a commit
      SHA, at a fixed uv version whose checksum the Action verifies
      from its own built-in list or a `checksum` input in the workflow,
      never skipped
- [ ] Every job in `ci.yaml` and `release.yaml` sets up Python 3.12
- [ ] `release.yaml` has no `twine check` step and installs no twine
- [ ] `[build-system] requires` in `pyproject.toml` names no exact
      version
- [ ] `PyYAML` and `requests` keep minimum versions in
      `[project.dependencies]`
- [ ] `ci.yaml` uploads coverage to Coveralls with the `coveralls`
      package from `uv.lock`, in a dependency group only that job
      installs, and no workflow uses `coverallsapp/github-action`
- [ ] `.github/dependabot.yml` adds the `uv` ecosystem with the same
      weekly schedule, single group and 14-day cooldown as actions,
      updates `uv.lock` versions and hashes together, and never raises
      the minimums in `pyproject.toml`
- [ ] Every test file has the import-group comments `python.md`
      requires; today `tests/markdown/test_utils.py` and six files in
      `tests/linter/rules/` lack them
- [ ] CI passes on the pull request, and a manual `Release` run on the
      branch builds and passes the TestPyPI install check
- [ ] The CI, testing and releasing wiki pages describe the dependency
      groups, `uv.lock` and the command that regenerates it,
      Dependabot's `uv` updates, and the local setup command

## Design Decisions

- Ruff is out of scope; it is its own backlog entry, `ruff-migration`
  (user, 2026-11-06).
- Runtime dependencies (`PyYAML`, `requests`) keep minimum versions in
  `[project.dependencies]` and are never pinned exactly there, since
  tiredize installs into other people's environments (user, from the
  backlog entry).
- Build tools are locked for CI and releases through the lock, not in
  `[build-system]`, so people building from source are not bound by
  them (user, from the backlog entry).
- Dependabot's updates use the same weekly schedule, grouping and
  14-day cooldown as actions (user, from the backlog entry).
- Every package the workflows install is pinned to an exact version
  and checked against its sha256 hash, nested dependencies included,
  for protection from supply-chain attacks (user, 2026-11-07).
- Development and release tools are declared as PEP 735 dependency
  groups, not extras, because groups are not published in the package
  metadata. The groups are the one place a tool is added or its
  minimum changed; the lock is generated from them and never edited by
  hand (user, 2026-11-08).
- Both workflows run Python 3.12, the newer of the two in use, so the
  lock covers one Python version (user, 2026-11-08).
- The wheel check and the TestPyPI install check in `release.yaml`
  install tiredize's dependencies from the lock too. The wheel check
  runs in the job that uploads the release files, and newer `PyYAML`
  and `requests` releases are tested through Dependabot's lock updates
  instead (user, 2026-11-08).
- uv generates and installs the lock, as `uv.lock`. Dependabot
  regenerates a compiled lock only from `.in` files, not from
  dependency groups, but updates `uv.lock` directly through its `uv`
  ecosystem, so uv is the only choice that keeps the groups as the one
  place to edit (user, 2026-11-08).
- `twine check --strict` is dropped. The publish Action runs
  `twine check` before the TestPyPI upload, which comes before PyPI,
  and twine adds about 25 packages to the lock; only the warnings-level
  strictness is lost (user, 2026-11-08).
- Coverage goes to Coveralls through the `coveralls` package (PyPI,
  maintained by Kevin James, not by Coveralls), not the Coveralls
  Action. The Action downloads its reporter program at run time,
  `latest` by default, checked only against a checksum from the same
  release; the package is hash-checked from the lock and updated by
  Dependabot. Codecov was considered and gains nothing over this
  (user, 2026-11-08).
- Scoping seeds: the work changes the development and release contract
  (how tools are declared, locked, installed and updated), so the
  technical reference is expected to change. User-facing documentation
  is expected too: the README's development section tells people to
  `pip install pytest pytest-cov flake8`.

- Contributors set up with `uv sync`, so a local environment matches
  CI's locked versions; uv is a requirement for working on tiredize
  (user, 2026-11-08).
- uv 0.13.5 is installed on the maintainer's machine for this work, the
  newest release at least 14 days old, hash-checked from PyPI into its
  own venv at `~/.local/venvs/uv` and linked from `~/.local/bin`
  (user approved the install, 2026-11-08).
- Acceptance tests are in `tests/test_tooling.py` (fe9ca97). Criteria
  14 and 15 are verification checks; the build versions in a run's
  log, the setup-uv checksum log, the first Dependabot `uv` PR and
  `uv lock --check` are verification checks too; every other criterion
  is a regression test. The workflow tests stay regression tests
  although they read `run:` steps heuristically, because installing
  only from the lock is the supply-chain invariant (user, 2026-11-08).
- Criterion readings (user, 2026-11-08): "every job" sets up Python
  3.12 means every job that runs Python tooling, so `tag-guard` and the
  publish jobs are exempt; "never raises the minimums" means
  Dependabot's `versioning-strategy: lockfile-only`; "hashes checked"
  means `--require-hashes` on `-r` installs and `--locked` or
  `--frozen` on `uv sync`, `uv run` and `uv export`.

## Open Questions

None.
