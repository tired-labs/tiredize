# Specification: Issue File Format

## Overview

This specification defines the structure, sections, and conventions
for issue files. It describes what an issue file contains and how
each section is formatted. For how issues move through statuses and
the completion pipeline, see `issue-lifecycle.md`.

Issue files live in `.context/issues/` and are named with lowercase,
hyphen-separated descriptive names (e.g., `markdown-schema-validation.md`).
The filename drives the branch name: `issue/<filename-without-extension>`.

## Format Principles

- **Human-readable prose** for context, motivation, and reasoning
  (Summary, Design Decisions, Open Questions). These sections explain
  the "why" and are primarily for human review.
- **Agent-optimized checklists** for actionable items (Acceptance
  Criteria, Out of Scope). These sections define the "what" and are
  structured for agents to parse, track, and update.

## Frontmatter

Every issue file begins with a YAML frontmatter block. This is the
machine-readable metadata for the issue, easily extracted by tooling
or any YAML parser. Frontmatter enables CI/CD pipelines, git hooks,
and agents to inspect issue state without parsing the document body.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Current issue status. One of: `draft`, `ready`, `active`, `blocked`, `done`, `cancelled`. |
| `type` | string | Nature of the work. One of: `bug`, `feature`, `refactor`, `documentation`, `spike`. |
| `priority` | string | Scheduling priority. One of: `critical`, `high`, `medium`, `low`. |
| `created` | string | Date the issue was created. ISO 8601 format: `YYYY-MM-DD`. |

### Optional Fields

| Field | Type | When to include |
|-------|------|-----------------|
| `parent` | string | Child issues only. Filename of the parent issue (e.g., `agent-workforce.md`). |
| `sub_issues` | list | Parent issues only. Filenames of child issues. |
| `specs` | list | When the issue affects one or more specification files. Filenames of affected specs (e.g., `git-workflow.md`). Acts as a mutex: two issues listing the same spec should not be `active` simultaneously to prevent concurrent modifications and inconsistent spec updates. |
| `labels` | list | Free-form tags for categorization and filtering (e.g., `agent-workforce`, `tooling`, `infrastructure`). |

Additional fields may be added as future needs arise. The frontmatter
block is the designated location for any structured metadata that
tools or pipelines need to extract.

### Examples

Standalone issue:
```yaml
---
status: draft
type: bug
priority: high
created: 2026-03-03
---
```

Parent issue with labels:
```yaml
---
status: active
type: feature
priority: high
created: 2026-02-28
sub_issues:
  - safeguard-audit.md
  - role-design-and-specifications.md
labels:
  - agent-workforce
  - architecture
---
```

Child issue:
```yaml
---
status: draft
type: feature
priority: medium
created: 2026-03-01
parent: agent-workforce.md
---
```

## Sections

The table below defines all sections in document order. Required
sections must be present in every issue file regardless of status.
Optional sections are included only when applicable.

| Order | Section | Level | Required | Purpose |
|-------|---------|-------|----------|---------|
| 1 | *(issue title)* | H1 | Yes | Descriptive name of the work. Not a literal section heading -- the issue's title rendered as a level 1 heading (e.g., `# Safeguard Audit`). |
| 2 | Summary | H2 | Yes | One or two sentences. What this work is and why it exists. Human-readable prose. |
| 3 | Acceptance Criteria | H2 | Yes | Enumerated checkbox list. Each item is a testable, verifiable statement of required behavior. |
| 4 | Test Specifications | H2 | No | Issues that go through the QA Engineer pipeline (coding work). Contains the test plan derived by the QA Engineer in step 1 of the completion pipeline. See Test Specifications Format below. |
| 5 | Out of Scope | H2 | Yes | What is explicitly excluded. Prevents scope creep. Always includes the standard preamble. |
| 6 | Domain Specific Sections | H2 | No | Container for domain-specific content. Child sections (H3) have freeform names and cover technical specifications, data formats, algorithms, error handling, API contracts -- whatever the nature of the work demands. |
| 7 | Design Decisions | H2 | Yes | Decisions made during implementation. Empty until work begins. |
| 8 | Open Questions | H2 | Yes | Unresolved items that block implementation. Must be empty for `ready` status. |
| 9 | References | H2 | No | External documents, specifications, or resources that informed the design. |
| 10 | Completion Report | H2 | Yes | Present from issue creation with all subsections. Progress checklist tracks pipeline state. Subsections are populated as the completion pipeline progresses. See Completion Report Structure below. |

### Test Specifications Format

The Test Specifications section is a checklist of tests the QA Engineer
derives from the acceptance criteria and relevant specifications. Each
entry is a checkbox that the Software Engineer checks off as they
implement the test. The QA Engineer writes the specs; the SE implements
them.

```markdown
## Test Specifications

- [ ] `test_name`
  - Purpose: What this test validates
  - Input: The input or setup conditions
  - Expected: The expected behavior or result
```

This section is distinct from the Test Summary in the Completion
Report. Test Specifications are the plan (what tests to write, defined
pre-implementation). The Test Summary is the result (what passed or
failed, populated post-implementation).

## Acceptance Criteria Standards

Acceptance criteria are the sole measure of progress. Each criterion
must be:

- **Testable** -- There is a concrete way to verify the criterion is
  met (a test passes, a file exists, a behavior is observable).
- **Verifiable** -- An independent reviewer can confirm the criterion
  is satisfied without needing to ask the implementer.
- **Specific** -- The criterion describes a concrete deliverable or
  behavior, not a vague goal. "Schema loader validates required
  fields" is specific. "Schema handling works correctly" is not.
- **Independent** -- Each criterion can be checked off on its own.
  Completing one does not implicitly complete another.

Draft issues may have partially formed criteria that are refined
during design sessions. However, even in draft, criteria should
describe observable outcomes, not implementation steps.

Criteria that describe implementation steps ("Write a function that
parses X") should be rewritten as behavioral outcomes ("Parser
extracts X from input and returns Y").

## Completion Report Structure

The Completion Report section is present in every issue from creation.
All subsections exist from the start with empty content. The progress
checklist tracks pipeline state and is populated as the completion
pipeline progresses. This structure can be extracted by tooling for
CI/CD pipeline automation.

For which roles populate which subsections and when, see the
completion pipeline in `issue-lifecycle.md`.

```markdown
## Completion Report

### Progress

- [ ] Implementation complete
- [ ] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [ ] User accepted

### Problem

What problem or need prompted this work.

### Solution

What was implemented and how it addresses the problem.

### Test Summary

| Test | Covers | Result |
|------|--------|--------|
| test_name | What it validates | Pass/Fail |

Total: N tests, N passed, N failed.

### Coverage

Coverage statistics for new or modified source files. Note any
uncovered lines and why.

### SE Peer Review

#### Incorporated

Summary of findings that were fixed during the peer review loop.

#### Not Incorporated

Any findings deferred or declined, with reasoning for each.

### QA Engineer Review

#### Incorporated

Summary of findings that were fixed during test validation.

#### Not Incorporated

Any findings deferred or declined, with reasoning for each.

### Technical Architect Review

#### Incorporated

Findings that were fixed during systemic review.

#### Not Incorporated

Any findings deferred or declined, with reasoning for each.

### Follow-Up Work

Bugs, tasks, or gaps discovered that need separate issues. Link to
issue files if created.

### Breaking Changes

Any changes to public behavior, CLI interface, configuration format,
or cross-subsystem contracts that could affect existing users or
downstream code. "None" if not applicable.

### Process Feedback

Process improvements identified by any role during the completion
pipeline. Each entry describes friction encountered and a suggested
improvement. Do not re-report suppressed items listed in CLAUDE.md.
```

## File Conventions

### Naming

Issue files use lowercase, hyphen-separated descriptive names:
`markdown-schema-validation.md`, `safeguard-audit.md`.

The filename drives the branch name:
`issue/<filename-without-extension>`.

### Location

All issue files live in `.context/issues/`.

## Design Decisions

- **Format principles split by audience.** Human-readable prose for
  context sections (Summary, Design Decisions, Open Questions) and
  agent-optimized checklists for actionable sections (Acceptance
  Criteria, Out of Scope). This dual-audience approach means both
  humans and agents can efficiently consume the parts they need.
- **Completion report present from creation.** All subsections exist
  from the start with empty content rather than being added as work
  progresses. This makes the structure predictable and extractable
  by tooling at any point in the issue's lifecycle.
- **Frontmatter for machine-readable metadata.** YAML frontmatter
  separates structured data (status, parent, specs) from the document
  body. This enables tools to inspect issue state without parsing
  Markdown.
- **Specs field as mutex.** Two issues listing the same spec in their
  `specs` frontmatter should not be `active` simultaneously. This
  prevents concurrent modifications and inconsistent spec updates.
- **File format split from lifecycle.** The structure of an issue file
  (what sections it contains, how frontmatter is formatted) is a
  different concern from how issues move through statuses and the
  completion pipeline. Separating them means agents creating or
  editing issue files only need the format spec, while agents
  orchestrating workflow only need the lifecycle spec.
