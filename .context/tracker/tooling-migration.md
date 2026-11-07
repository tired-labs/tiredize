---
assignee:
created: 2026-11-06
knowledge: []
priority: high
status: draft
step:
tags: []
type: refactor
workflow: software-engineering
---

# Pin CI and release tools and keep them current with Dependabot

## Summary

`ci.yaml` and `release.yaml` install pip, build, twine, flake8, pytest,
pytest-cov and the build backend (hatchling, hatch-vcs) unpinned, so
each run gets whatever is newest. An unpinned hatchling 1.33.0 is what
broke the first TestPyPI upload. Pin every tool both workflows install,
have Dependabot propose updates to the pins, and tidy the development
setup around them: declare the development tools as a `dev` extra in
`pyproject.toml`, stop installing the unused `coveralls` package, and
finish the import-grouping comments in the test files that lack them.

Dependabot's `pip` ecosystem updates any `.txt` requirements-style file
and PEP 621 `[project]` tables, but has no confirmed support for
`[build-system] requires`, so the pins live in a constraints file.

This issue updates these wiki pages:

- [CI](../wiki/practices/ci.md)
- [testing](../wiki/practices/testing.md)
- [releasing](../wiki/operations/releasing.md)

## Acceptance Criteria

- [ ] One constraints file in the repository pins an exact version of
      every tool `ci.yaml` and `release.yaml` install: pip, build,
      twine, flake8, pytest, pytest-cov, hatchling and hatch-vcs
- [ ] Both workflows install their tools through the constraints file,
      and `python -m build` in `release.yaml` builds with the pinned
      hatchling and hatch-vcs, shown by the versions in a run's log
- [ ] `[build-system] requires` in `pyproject.toml` names no exact
      version
- [ ] `pyproject.toml` declares a `dev` extra listing the test and lint
      tools with minimum versions only, and CI installs tiredize with
      `.[dev]`
- [ ] `PyYAML` and `requests` keep minimum versions in
      `[project.dependencies]`
- [ ] No workflow installs `coveralls`
- [ ] `.github/dependabot.yml` adds the `pip` ecosystem with the same
      weekly schedule, single group and 14-day cooldown as actions, and
      is configured so it never raises the runtime dependency minimums
- [ ] Every test file has the import-group comments `python.md`
      requires; today `tests/markdown/test_utils.py` and six files in
      `tests/linter/rules/` lack them
- [ ] CI passes on the pull request, and a manual `Release` run on the
      branch builds and passes the TestPyPI install check
- [ ] The CI, testing and releasing wiki pages describe the pins, how
      to update them, Dependabot's `pip` updates, and the local setup
      command

## Design Decisions

- Ruff is out of scope; it is its own backlog entry, `ruff-migration`
  (user, 2026-11-06).
- Runtime dependencies (`PyYAML`, `requests`) keep minimum versions and
  are never pinned exactly, since tiredize installs into other people's
  environments (user, from the backlog entry).
- Build tools are pinned for CI and releases through the constraints
  file, not in `[build-system]`, so people building from source are not
  bound by them (user, from the backlog entry).
- Dependabot's `pip` updates use the same weekly schedule, grouping and
  14-day cooldown as actions (user, from the backlog entry).

## Open Questions

- Does the constraints file pin only the tools named above, or every
  package the workflows install, including the tools' own dependencies
  (pyflakes, coverage, pluggy and so on) and the runtime dependencies
  in CI? Pinning everything makes runs reproducible; pinning only the
  named tools keeps the file short and lets CI test against new
  `PyYAML` and `requests` releases as users would get them.
