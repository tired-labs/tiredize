---
assignee:
created: 2026-09-18
knowledge: []
priority: low
status: draft
step:
tags: [linter]
type: bug
workflow: software-engineering
---

# `links` Rule Crashes on a Malformed URL When `exclude` Is Configured

## Summary

`_is_excluded()` in `tiredize/linter/rules/links.py` calls
`urlparse(url).hostname`, which raises `ValueError` for URLs the
standard library cannot parse — an unclosed IPv6 bracket such as
`http://[::1` is the known case. The exception escapes the rule, so a
document containing one malformed link aborts the whole run with a
traceback instead of a finding, but only when the rule's `exclude`
option is configured; without it `_is_excluded()` returns before
parsing.

Found by the software-engineer at step 3 of `autolink-gfm-parity`
during a smoke run. Pre-existing on `main`; not introduced by that
issue. A skipped regression test,
`tests/linter/rules/test_links.py` with
`reason="links-exclude-malformed-url-crash: …"`, records the expected
behaviour (no exception; the link is reported as a finding) and is to
be unskipped by this issue.

## Acceptance Criteria

- [ ] A malformed URL with `exclude` configured produces a finding, not
      an exception
- [ ] The skipped regression test is unskipped and passes
- [ ] Full test suite passes

## Design Decisions

Not yet scoped. Whether the malformed link should be reported by the
rule (as "not reachable" with the parse error as the message) or
handed to `check_url_valid()` to report is the one design question;
the contract for the finding message should be settled at scoping.

## Open Questions

## Comments

### 2026-09-18T16:00:00+00:00

Author: program-manager

    Filed so that the skipped regression test added under
    `autolink-gfm-parity` names an issue that exists. Draft until
    scoped.
