Status: draft
Parent: gfm-parity.md

# GFM Parity: Indented Code Blocks

## Summary

Implement indented code block support. GFM spec section 4.4 defines
indented code blocks as consecutive lines indented with 4 or more
spaces (or 1 tab). These are distinct from fenced code blocks
(backtick/tilde fences) and have no language identifier.

The parser currently only supports fenced code blocks. Lines with
4+ space indentation are treated as plain text content.

## GFM Spec Reference

Section 4.4 — Indented code blocks

## Acceptance Criteria

- [ ] (to be filled during scoping)
