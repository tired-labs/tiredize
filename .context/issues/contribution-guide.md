---
assignee:
created: 2026-09-14
knowledge: []
priority: medium
status: draft
step:
tags: [pr-44, process]
type: documentation
workflow: documentation
---

# Author a Contribution Guide

## Summary

The project has no `CONTRIBUTING.md`. External contributors have no
documented guidance on how work should arrive, which produced PR #44:
two unrelated changes in one pull request, raised from the contributor's
fork `main`, with no issue describing the problem being solved or the
approach taken.

The cost falls on the maintainer. Without a stated problem, reviewing an
inbound PR means reconstructing the intent from the diff, then assessing
whether the solution is complete against a specification that was never
written down. That is slow, and it is the wrong order of operations.

A guide was committed to publicly in the PR #44 review comment, so this
is an outstanding promise to a contributor, not just an internal
improvement.

## Acceptance Criteria

- [ ] `CONTRIBUTING.md` exists at the repository root, where GitHub
      surfaces it automatically in the issue and pull request flows
- [ ] States the issue-first policy: pull requests must reference an
      open issue that identifies the problem, with minor bug fixes
      exempt
- [ ] Defines what qualifies for the minor-fix exemption clearly enough
      that a contributor can self-assess without asking
- [ ] States one change per pull request
- [ ] States that contributions should be raised from a topic branch,
      not the contributor's fork `main`, and explains why — squash
      merges make already-merged commits reappear in later diffs
- [ ] Covers contributions that touch `.context/`: contributors may edit
      specifications, and the technical-architect reviews the edit
      rather than replacing it
- [ ] Covers local development: editable install, running the test
      suite, running flake8
- [ ] README links to the guide
- [ ] Existing open pull requests are not retroactively held to it

## Design Decisions

- Filename is `CONTRIBUTING.md`, not `CONTRIBUTORS.md`. GitHub surfaces
  the former automatically when a contributor opens an issue or pull
  request; the latter conventionally means a credits list.
- Contributors may author changes to `.context/specifications/`. The
  technical-architect reviews the edit as it would review code, rather
  than discarding it and rewriting. Decided 2026-09-11. Accepted risk:
  `.context/` drifting in voice and structure from the dotclaude
  templates.
- The issue-first policy carries a minor-fix exemption deliberately.
  Gating every typo behind an issue is friction with no return, and
  would have rejected the genuine bug report inside PR #44.

## Open Questions

- **Which tracker do contributors use?** The policy stated in PR #44 is
  that pull requests must be associated with an open issue. The project
  has no GitHub issues at all, and its inventory lives as markdown files
  in `.context/issues/`. An external contributor cannot open one there
  without a pull request, and GitHub will not link a pull request to a
  file path. The guide cannot state the policy until this is resolved.
  Options: mirror work items into GitHub issues; make GitHub issues the
  contributor-facing front door and convert accepted ones into
  `.context/issues/` work items; or direct contributors to reference
  `.context/issues/` by path and accept that GitHub shows no link.
- Where exactly does the minor-fix exemption end? A one-line regex
  change was the trigger for this issue and was *not* minor, because it
  altered documented behaviour. "Small diff" is the wrong test;
  "changes documented behaviour, the schema, or a specification" is
  closer, but needs stating in language a contributor can apply.
- `AGENTS.md` has no knowledge mapping for the `documentation` workflow
  steps, so every agent on this issue would run on base function alone.
  The step files name `markdown-style` and `ai-prose-hygiene`, and both
  exist in the config repository. The mapping should be added before
  this issue is worked.

## Comments

### 2026-09-14T00:00:00+00:00

Author: program-manager

    Created following the PR #44 review. The maintainer stated the
    policy to the contributor directly: all pull requests to be
    associated with an open issue where the problem is well identified,
    minor bug fixes exempt. This issue exists so that commitment is
    tracked rather than left in a PR comment thread.
