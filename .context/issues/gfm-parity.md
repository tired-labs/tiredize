Status: draft
Parent: test-coverage-audit.md

# GFM Parity: Unsupported Syntax Variants

## Summary

The markdown parser does not handle several syntax variants that are
valid in GitHub-Flavored Markdown. These were identified during the
syntax variant audit (`test-coverage-markdown-types.md`) and are
currently documented as skipped spec tests. This issue tracks adding
support for them to achieve closer GFM parity.

52 skipped spec tests across all element types document the gaps.

## Findings

### CodeBlock (6 skips)

- Tilde-fenced code blocks (`~~~` delimiter) not matched. Regex only
  handles backtick fences.
- Indented code fences (1-3 spaces before ```) not matched.
  Start-of-line anchor requires no leading whitespace.
  Two tests cover this (general + 1-space specific).
- Closing fence with trailing spaces not matched. Backreference `\1`
  requires exact delimiter match.
- Empty code block (zero content lines: ```` ```\n``` ````) not
  matched. Pattern requires `\n` before closing fence but no content
  newline exists.
- CRLF line endings cause complete match failure. Pattern uses
  literal `\n`.

### CodeInline (4 skips)

- Double-backtick inline code (``` `` code `` ```) not matched.
  Pattern only handles single-backtick delimiters.
- Triple-backtick inline code not matched. Same issue.
- Inline code containing a single backtick (multi-backtick wrapper)
  not supported. Would require matching balanced multi-backtick
  delimiters.
- Multiline inline code (`\`foo\nbar\``) not matched.
  Character class `[^\n\`]` excludes newlines.

### Header (5 skips)

- Closing hashes (`# Heading ##`) not stripped from title.
  `[^\n]+` captures trailing `#` characters as part of title text.
- Empty heading (`# ` with only whitespace after hash) not matched.
  `[^\n]+` requires at least one content character after `\s+`
  consumes the space.
- Leading spaces (1-3 before `#`: `   # Heading`) not matched.
  Start-of-line anchor requires `#` immediately after newline.
- Setext headings (`Heading\n=======` and `Heading\n-------`) not
  matched. Parser only handles ATX-style. Two tests cover equals
  and dash underlines.

### InlineLink (6 skips)

- Single-quote title (`[t](url 'title')`) not captured.
  Regex only matches double-quoted titles.
- Parenthesis title (`[t](url (title))`) not captured.
- Angle-bracket URL (`[t](<url with spaces>)`) not matched.
  `\S+` cannot handle spaces.
- Empty URL (`[text]()`) not matched. `\S+` requires at least one
  character.
- Escaped brackets in link text (`[text \] here](url)`) broken.
  `[^]]*?` stops at first `]`, no escape handling.
- Nested brackets in link text (`[text [nested]](url)`) broken.
  Same `[^]]` issue.
- Escaped quote in title (`"title \" here"`) truncated.

### BracketLink (2 skips)

- Non-HTTP schemes (`<ftp://example.com>`, `<mailto:user@host>`)
  not matched. Pattern requires `https?://`.
- Email autolinks (`<user@example.com>`) not matched.

### BareLink (3 skips)

- `www.` prefix without scheme not matched. Pattern requires
  `http[s]?://` or `./` or `\`.
- Trailing punctuation (`https://example.com.`) captured as part of
  URL. GFM strips trailing punctuation from extended autolinks.
- Relative paths with `../` prefix produce false partial match.
  `./` inside `../` is matched starting at position 1.

### InlineImage (5 skips)

- Greedy URL regex consumes past closing paren in adjacent syntax
  (`![img](a.png)[link](b.html)` -- URL becomes `a.png)[link](b.html`).
- Single-quote title not captured (same as InlineLink).
- Angle-bracket URL not matched (same as InlineLink).
- `]` in alt text breaks match (same as InlineLink text).
- Empty URL not matched (same as InlineLink).
- Escaped quote in title truncated (same as InlineLink).

### ReferenceDefinition (4 skips)

- Single-quote title not captured.
- Angle-bracket URL (`[ref]: <url>`) not matched.
- URL without `#`, `.`, or `/` (`[ref]: example`) rejected by
  pattern `\S*[#\.\/]+\S*`.
- Indented definition (1-3 spaces) not matched.
- `]` in label breaks match.

### LinkReference (2 skips)

- Collapsed reference (`[text][]`) detected as shortcut reference
  instead. `text` field is None instead of content.
- `]` in reference label breaks match.

### ImageReference (3 skips)

- Collapsed image reference (`![alt][]`) same issue as LinkReference.
- `]` in reference label breaks match.

### Table (2 skips)

- Escaped pipes (`\|`) in cells cause over-split. `split("|")`
  does not handle backslash escapes.
- CRLF line endings cause complete match failure.

### QuoteBlock (3 skips)

- Lazy continuation (`> first\nsecond` as single quote) not matched.
  Only lines starting with `>` are captured.
- Spaced nested quotes (`> > nested`) parsed as depth 1.
  Pattern `[>]+` requires consecutive `>` without spaces.
- Indented block quote (`   > quote`) not matched.

### FrontMatter (4 skips)

- `...` (three dots) closing delimiter not matched.
- Empty frontmatter (`---\n---\n`) not matched.
- More than 3 dashes (`----`) not matched. `[-]{3}` matches
  exactly 3.
- CRLF line endings cause complete match failure.
- Leading whitespace on delimiter not matched (this is actually
  correct behavior for most implementations).

### CRLF data quality (not skipped, documented as actual behavior)

Several types match with CRLF input but capture `\r` as content:
- Header titles include trailing `\r`
- QuoteBlock quotes include trailing `\r`
- CodeInline content includes `\r`
- ReferenceDefinition matches succeed (CRLF doesn't break the
  match because `\s*?` absorbs `\r`)

## Acceptance Criteria

- [ ] Each variant is evaluated for implementation feasibility and
      priority
- [ ] Regex patterns updated to handle accepted variants
- [ ] Existing skipped spec tests unskipped after fixes land and
      tests pass
- [ ] New tests added for each newly supported variant
- [ ] Parser specification updated to reflect supported syntax

## Out of Scope

- CRLF line ending handling (cross-cutting concern, may warrant its
  own issue)
- Pipe-as-start-of-line anchor behavior (design decision to evaluate
  separately)
- Missing sanitization chains (tracked in
  `parser-sanitization-gaps.md`)
- sanitize_text trailing newline bug (tracked in
  `sanitize-text-newline-bug.md`)
- QuoteBlock over-sanitization (tracked in
  `quoteblock-over-sanitization.md`)
- Greedy regex patterns (tracked in `parser-greedy-regex.md`)

## Design Decisions

## Open Questions

- Should these be tackled as a single issue or split by category
  (block-level, inline, links, other)?
- What is the priority order? Which variants do real-world documents
  most commonly use?
- Should CRLF handling be addressed here or as a separate
  cross-cutting issue since it affects every pattern?
