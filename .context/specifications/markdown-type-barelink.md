# Specification: BareLink

**GFM Equivalent:** Extended autolinks (GFM spec section 6.9,
GFM extension)
**Source File:** `tiredize/markdown/types/link.py`
**GFM Compliance:** Partial

## Description

A bare link is a URL that appears in text without any enclosing
syntax (no brackets, no parentheses). The parser matches absolute
HTTP/HTTPS URLs, parent-relative paths (`../`), and current-relative
paths (`./` or `\`).

BareLink has the deepest sanitization chain of any extractor because
bare URLs are the most ambiguous pattern and must exclude all other
link and reference types.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text |
| `url` | `str` | The captured URL |

## Regex Pattern

```
(?P<url>
    (http[s]?:\/\/      # Absolute URL: http:// or https://
    |(\.\.\/)           # Parent-relative path: ../
    |(\.\/|\\)          # Current-relative path: ./ or \ (Windows)
    )\S+                # Rest of URL: any non-whitespace
)
```

The `../` alternative appears before `./` to prevent `./` from
false-matching at position 1 inside `../` paths. See the hub spec
"BareLink Relative Path Matching" section. `\S+` is used (not
`[^\s)]+`) because bare links have no closing delimiter to consume
past.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline, InlineImage,
BracketLink, InlineLink, ReferenceDefinition
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets.

## GFM Compliance

Partial compliance with GFM spec section 6.9. Known gaps:

- `www.` prefix without scheme not matched. Pattern requires
  `http[s]?://` or `./` or `\`.
- Trailing punctuation (`https://example.com.`) captured as part
  of URL. GFM strips trailing punctuation from extended autolinks.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| BareLink | Extended autolink (extended www autolink, extended URL autolink) |

## Notes

- Defined in the same source file as InlineLink and BracketLink
  (`link.py`).
- The deep sanitization chain ensures bare URLs inside inline
  links, images, bracket links, and reference definitions are not
  double-matched.
- Relative path matching (`./`, `../`, `\`) is a tiredize extension
  not present in the GFM spec. It supports linting of local file
  references in documentation projects.
