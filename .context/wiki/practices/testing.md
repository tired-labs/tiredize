# Testing

## Overview

How tiredize is tested and what a change must keep passing. Where test
files live is on [repository layout](../repository/layout.md); what CI
runs is on [CI](./ci.md).

## Running

```bash
pip install -e .
pip install pytest pytest-cov flake8
flake8 tiredize tests
pytest --cov=tiredize
```

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
- **Coverage aims at 100%.** A line is excluded only when it is
  unreachable, with the reason written in the test file. The target is
  not enforced: CI sets no threshold.
- **`__main__.py` is covered in-process** with `runpy.run_module` and a
  patched `sys.argv`, not by subprocess coverage, which needs extra
  machinery and tends to be flaky.
- **Real documents are checked by hand.** Changes to the parser or the
  schema validator are also run against the TRRs in the techniques
  repository; that is how the table backtracking hang was found.

## Design Decisions

- **Skipped tests as the record of known gaps,** so the gap and its
  fix are tied to a test and a slug rather than to prose that drifts.
- **Pinned specification examples are the record of GFM parity,**
  instead of a copy of the specification kept in the repository.
