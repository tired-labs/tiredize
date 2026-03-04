---
status: draft
type: feature
priority: medium
created: 2026-03-03
---

# Container Element Model

## Summary

Several GFM element types are containers — their content is real
markdown that should be parsed into child elements. The current
parser treats all element types as leaf nodes with opaque string
content. This means the AST does not represent the document tree
accurately: a QuoteBlock with a link inside it has no structural
relationship to that link.

This issue tracks redesigning container types to parse their content
into child elements, producing a richer AST that reflects the actual
document structure per GFM.

## Acceptance Criteria

- [ ] GFM spec reviewed to identify all container element types and
      which child types are valid inside each
- [ ] Container types redesigned to parse content into child elements
- [ ] Child element positions are correct relative to the document
      root (not relative to the container's content)
- [ ] Downstream consumers (linter rules, schema validator) updated
      to traverse into container children where appropriate
- [ ] Parser specification updated to document container model
- [ ] No regressions in existing tests

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- GFM syntax variant support (tracked in `gfm-parity.md`)
- Sanitization chain changes unrelated to the container model

## Domain Specific Sections

### GFM Container Types to Evaluate

The following types may qualify as containers per GFM. Each needs to
be evaluated against the GFM spec to determine whether it should
parse child elements and which child types are valid.

- **QuoteBlock** — GFM block quotes are containers. Content after
  `> ` is real markdown: links, images, inline code, nested quotes,
  and even other block-level elements (lists, code blocks, headers)
  can appear inside.

- **Table cells** — GFM table cells support inline content: links,
  images, inline code, emphasis. Block-level elements are not valid
  inside table cells per GFM.

- **List items** — GFM list items are containers that support both
  inline and block-level content (paragraphs, nested lists, code
  blocks, blockquotes). This is one of the most complex container
  types in GFM.

- **Other candidates** — Evaluate whether any other GFM elements
  have container semantics that the current parser treats as leaf
  nodes.

## Design Decisions

## Open Questions

- Which child types are valid inside each container? GFM allows
  different content in different containers (e.g., table cells only
  allow inline content, list items allow block-level content).
- How should child positions be tracked? Children need document-root
  offsets, but extraction happens on stripped content (e.g., after
  removing `> ` prefix). The `base_offset` threading pattern used by
  Section may apply here.
- Should container parsing reuse the existing extractor methods, or
  does it need a separate extraction pass?
- How does this interact with Section._extract() orchestration?
  Currently Section is the only element that has children. Adding
  more container types may require rethinking the extraction order.
- Do linter rules need to traverse into container children? For
  example, should a link-checking rule find links inside blockquotes
  and table cells?

## Completion Report

This issue predates the current issue file format. Completion report
sections will be populated if the issue is revisited.

### Progress

- [ ] Implementation complete
- [ ] SE peer review passed
- [ ] QA Engineer review passed
- [ ] Technical Architect review passed
- [ ] Director review passed
- [ ] User accepted

### Problem

### Solution

### Test Summary

### Coverage

### SE Peer Review

#### Incorporated

#### Not Incorporated

### QA Engineer Review

#### Incorporated

#### Not Incorporated

### Technical Architect Review

#### Incorporated

#### Not Incorporated

### Follow-Up Work

### Breaking Changes

### Process Feedback
