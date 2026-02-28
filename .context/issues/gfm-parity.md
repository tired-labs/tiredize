Status: draft

# GFM Parity: Unsupported Syntax Variants

## Summary

The markdown parser does not handle several syntax variants that are
valid in GitHub-Flavored Markdown. These were identified during the
syntax variant audit (`test-coverage-markdown-types.md`) and are
currently documented as unsupported. This issue tracks adding support
for them to achieve closer GFM parity.

## Variants

### Block-level

- Indented code blocks (4-space or 1-tab indentation without fences)
- Tilde-fenced code blocks (`~~~` delimiter)
- Unclosed code fences (GFM extends to end of document)
- Setext headings (underline style: `Heading\n=======` and
  `Heading\n-------`)
- Lazy continuation in block quotes (continuation lines without
  repeating `>`)
- Leading indentation (1-3 spaces) on block-level elements (code
  fences, headers, block quotes, reference definitions)

### Inline

- Multi-backtick inline code delimiters (``` `` code `` ```)
- Backslash-escaped characters (`\[`, `\]`, `` \` ``, `\>`, `\"`)
- Single-quote and parenthesis title delimiters in links/images
- Angle-bracket-enclosed URLs with spaces (`<url with spaces>`)
- Empty URLs in links and images (`[text]()`, `![alt]()`)

### Links and references

- GFM extended autolinks (`www.example.com` without scheme)
- Non-HTTP URI schemes in autolinks (`ftp://`, `mailto:`, `ssh://`)
- Email autolinks (`<user@example.com>`)
- Trailing punctuation stripping on extended autolinks
- Multi-line reference definitions (title on next line)
- Collapsed reference links (`[text][]`)

### Other

- TOML and JSON front matter (`+++` and `{}`-delimited)
- `...` (three dots) as YAML front matter closing delimiter
- HTML `<code>` elements

## Acceptance Criteria

- [ ] Each variant is evaluated for implementation feasibility and
      priority
- [ ] Regex patterns updated to handle accepted variants
- [ ] Existing characterization tests (from test coverage audit)
      updated to assert correct behavior after fixes
- [ ] New tests added for each newly supported variant
- [ ] Parser specification updated to reflect supported syntax

## Out of Scope

- CRLF line ending handling (cross-cutting concern, may warrant its
  own issue)
- Pipe-as-start-of-line anchor behavior (design decision to evaluate
  separately)

## Design Decisions

## Open Questions

- Should these be tackled as a single issue or split by category
  (block-level, inline, links, other)?
- What is the priority order? Which variants do real-world documents
  most commonly use?
- Should CRLF handling be addressed here or as a separate cross-cutting
  issue since it affects every pattern?
