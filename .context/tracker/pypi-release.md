---
assignee:
created: 2026-11-06
knowledge: []
priority: high
status: blocked
step:
tags: []
type: feature
workflow: software-engineering
---

# Publish tiredize to PyPI under the tired-labs organization

## Summary

Publish tiredize to the production PyPI, which a coworker has asked
for. Releases go only to TestPyPI today, so `pip install tiredize` in
the README does not work. Today's uploads also run as the user's old
personal account, through an API token stored as the GitHub Actions
secret `TEST_PYPI_API_TOKEN`; releases should be owned by and published
as the `tired-labs` organization instead.

Part of the work is done by the user in the PyPI and GitHub web
interfaces (organization, publisher and environment setup); the rest is
the release workflow and documentation.

This issue updates these wiki pages and files:

- [releasing](../wiki/operations/releasing.md)
- [installing and running](../wiki/operations/installing-and-running.md)
- [CI](../wiki/practices/ci.md)
- [README](../../README.md)

## Acceptance Criteria

- [ ] A `tired-labs` organization exists on pypi.org and owns the
      `tiredize` project
- [ ] A tagged release publishes to pypi.org from the `tired-labs/tiredize`
      repository without any long-lived token or password
- [ ] Publishing to pypi.org runs only from a protected GitHub
      environment
- [ ] The release workflow fails when the tag does not match `version`
      in `pyproject.toml`
- [ ] The `TEST_PYPI_API_TOKEN` secret is deleted and its token revoked
      on TestPyPI
- [ ] `pip install tiredize` in a clean environment installs the
      released version from pypi.org
- [ ] The wiki pages and README listed in the Summary describe the new
      release process

## Design Decisions

- The project is published and owned by the `tired-labs` PyPI
  organization, not a personal account (user, 2026-11-06).
- The user's personal pypi.org account (`daemorgue@tired-labs.org`) is
  live and requested the `tired-labs` organization on 2026-11-06; the
  request is pending PyPI approval.

## Open Questions

- Waiting on PyPI to approve the `tired-labs` organization.
- Authenticate with PyPI Trusted Publishing (GitHub OIDC, no stored
  secret)? Proposed by the PM, not yet confirmed. If adopted, it may
  shrink the `ci-secrets-in-aws` backlog entry.
- Keep TestPyPI as a dry run (for example on manual runs), or drop it?
  If kept, does the TestPyPI project also move to a `tired-labs`
  organization there?
- Is the name `tiredize` free on pypi.org?
- Should the `authors` field in `pyproject.toml` stay as is or name the
  organization?
