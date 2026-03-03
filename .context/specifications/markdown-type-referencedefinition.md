# Specification: ReferenceDefinition

**GFM Equivalent:** Link reference definitions (GFM spec section 4.7)
**Source File:** `tiredize/markdown/types/reference.py`
**GFM Compliance:** Partial

## Description

A link reference definition maps a label to a URL and optional title.
Written as `[label]: url "title"` at the start of a line. Reference
definitions are not rendered as visible content — they provide targets
for link references and image references elsewhere in the document.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text |
| `text` | `str` | The reference label between `[` and `]` |
| `title` | `str` | Optional title in double quotes (see Notes for type caveat) |
| `url` | `str` | The URL after the colon and whitespace |

## Regex Pattern

```
(?:(?<=\n)|(?:^))\[        # Start-of-line anchor + opening bracket
(?P<text>[^]]*?)           # Label text (lazy, excludes ])
\]:\s+                     # Closing bracket + colon + whitespace
(?P<url>\S*[#\.\/]+\S*)    # URL: must contain #, ., or /
\s*?                       # Optional whitespace
("(?P<title>[^"]*)")?      # Optional title in double quotes
(?=\n|$)                   # Lookahead: must end at newline or EOF
```

The URL pattern `\S*[#\.\/]+\S*` requires at least one `#`, `.`, or
`/` character. This prevents plain words from matching as URLs but
also means URLs without these characters are rejected. The
end-of-line lookahead ensures definitions don't consume content on
the same line.

## Sanitization

**Chain (in order):** CodeBlock
**Own sanitize():** Replaces entire match with whitespace,
preserving character offsets. Used by BareLink's sanitization chain
to prevent bare URL matching inside reference definitions.

## GFM Compliance

Partial compliance with GFM spec section 4.7. Known gaps:

- Single-quote title not captured. Regex only matches
  double-quoted titles.
- Angle-bracket URL (`[ref]: <url>`) not matched.
- URL without `#`, `.`, or `/` (`[ref]: example`) rejected by
  pattern `\S*[#\.\/]+\S*`.
- Indented definition (1-3 spaces) not matched. Start-of-line
  anchor requires `[` immediately after newline.
- `]` in label breaks match. `[^]]*?` stops at first `]`.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| ReferenceDefinition | Link reference definition |

## Notes

- Defined in the same source file as LinkReference and
  ImageReference (`reference.py`).
- The `title` field is declared as `str` in the dataclass but
  receives `None` at runtime when the optional title group does
  not match. The type annotation should be `str | None`. This is
  the same pre-existing type annotation inconsistency as in
  InlineLink.
