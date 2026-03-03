Status: draft
Parent: gfm-parity.md

# GFM Parity: Hard Line Breaks

## Summary

Implement hard line break support. GFM spec section 6.7 defines
hard line breaks as either two or more trailing spaces at the end
of a line, or a backslash (`\`) immediately before a line ending.

The parser currently has no element type for hard line breaks.
Trailing spaces and backslash-newline sequences are treated as
plain text.

## GFM Spec Reference

Section 6.7 — Hard line breaks

## Acceptance Criteria

- [ ] (to be filled during scoping)
