Status: draft
Parent: gfm-parity.md

# GFM Parity: Setext Headings

## Summary

Implement setext heading support. GFM spec section 4.3 defines
setext headings as one or more lines of text followed by a line
of `=` characters (level 1) or `-` characters (level 2). Examples:

```
Heading Level 1
===============

Heading Level 2
---------------
```

The parser currently only supports ATX-style headings (`# Heading`).
Setext headings are treated as plain text.

## GFM Spec Reference

Section 4.3 — Setext headings

## Acceptance Criteria

- [ ] (to be filled during scoping)
