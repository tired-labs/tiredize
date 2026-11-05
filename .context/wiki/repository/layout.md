# Repository Layout

## Overview

Where each kind of file lives in this repository, so changes land in
the right place.

## Layout

```
tiredize/                 the package
├── __main__.py           python -m tiredize
├── cli.py                command-line entry point
├── core_types.py         Position, RuleResult, RuleNotFoundError
├── linter/               engine, helpers and rules/ (one module per rule)
├── markdown/             parser: utils.py and types/ (one module per element)
└── validators/           markdown and frontmatter schema validators
tests/                    mirrors tiredize/
└── test_cases/           shared fixture documents and rules files
.github/workflows/        CI and release workflows
.context/wiki/            this wiki
.context/tracker/         work not yet done (backlog.md, issue files)
pyproject.toml            package metadata, dependencies, console script
README.md                 the user guide
```

Each component page under `components/` lists its own files.

## Conventions

- **Tests mirror the source tree.** `tiredize/foo/bar.py` is tested
  under `tests/foo/`. `tiredize/__main__.py` is tested by
  `tests/test_main_module.py`, because `test___main__.py` is unreadable.
  Not every module has exactly one test file: `code.py` is split across
  `test_codeblock.py` and `test_codeinline.py`, `link.py` also has
  `test_link_gfm_autolinks.py` for the pinned GFM examples, and
  `linter/engine.py` and `linter/rules/__init__.py` are tested by
  `tests/linter/rules/test_engine.py` and `test_loader.py`.
- **A new linter rule is a new module** in `tiredize/linter/rules/`
  (see [linter engine](../components/linter-engine.md)). A module whose
  name starts with `_` is private and is never loaded as a rule.
- **A new markdown element is a new module** in `tiredize/markdown/types/`
  following the element pattern on the [parser](../components/markdown-parser.md)
  page, plus a `Section` field and, if rules should see it, an entry in
  the element vocabulary.
- **Runtime dependencies** are declared in `pyproject.toml`:
  `PyYAML>=6.0` and `requests>=2.32.5`. Development tools (pytest, pytest-cov, flake8) are not
  declared there; CI installs them by name (see [CI](../practices/ci.md)).

## Design Decisions

- **The frontmatter schema loader and validator share one module,**
  unlike the markdown schema, whose data model lives in
  `markdown/types/schema.py`. The frontmatter model is flat and is not a
  markdown type.
