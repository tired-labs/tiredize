---
assignee:
created: 2026-03-02
knowledge: []
priority: medium
status: draft
step:
tags: []
type: feature
workflow: software-engineering
---

# GFM Parity: Unsupported Syntax Variants

## Summary

The markdown parser does not handle several syntax variants that are
valid in GitHub-Flavored Markdown. These were identified during the
syntax variant audit (`test-coverage-markdown-types`) and are
currently documented as skipped spec tests. This issue tracks adding
support for them to achieve closer GFM parity.

50 skipped spec tests across twelve element types document the gaps,
verified by `pytest -rs` on 2026-09-14. The whole set is too large to
carry as one unit of work, so it is delivered one element type at a
time.

## Acceptance Criteria

Each element type below is its own unit of work, taken up as a separate
issue tagged `gfm-parity` when it is scheduled. This issue is the
register: it closes when every element below is closed. The skip counts
are authoritative as of 2026-09-14 and each element's gaps are detailed
under Findings.

- [ ] **InlineLink** (7 skips) — titles, empty URLs, escaped and
      nested brackets, angle-bracket URLs
- [ ] **CodeBlock** (6 skips) — tilde fences, indented fences, closing
      fence whitespace, empty blocks, CRLF
- [ ] **InlineImage** (5 skips) — shares title and URL handling with
      InlineLink
- [ ] **ReferenceDefinition** (5 skips) — indentation, titles,
      angle-bracket URLs, `]` in label
- [ ] **Header** (5 skips) — closing hashes, empty headings, leading
      spaces, setext
- [ ] **FrontMatter** (5 skips) — `...` delimiter, empty content,
      4+ dashes, indentation, CRLF
- [ ] **CodeInline** (4 skips) — multi-backtick delimiters, multiline
- [ ] **QuoteBlock** (3 skips) — lazy continuation, spaced nesting,
      indentation
- [ ] **BareLink** (2 skips) — `www.` autolinks, trailing punctuation
- [ ] **BracketLink** (2 skips) — non-HTTP schemes, email autolinks
- [ ] **LinkReference** (2 skips) — collapsed references, `]` in label
- [ ] **ImageReference** (2 skips) — collapsed references, `]` in label
- [ ] **Table** (2 skips) — escaped pipes, CRLF

Criteria that span every element and are not delegated to a child:

- [ ] Parser specification updated to reflect supported syntax
- [ ] InlineLink and InlineImage URL patterns support balanced
      parentheses (e.g., `https://en.wikipedia.org/wiki/Foo_(bar)`)
      per GFM extended autolink spec
- [ ] Cross-component sanitization test audit: for each extractor
      with a sanitization chain, verify that tests exist confirming
      the extractor ignores matches inside each sanitized type's
      content (e.g., Table ignores table syntax inside code fences,
      InlineLink ignores URLs inside code blocks). Fill any gaps
      found.
- [ ] Every skipped spec test is either unskipped and passing, or
      documented as deliberately unsupported

## Design Decisions

Out of scope: CRLF line-ending handling (cross-cutting; may warrant its
own issue), and variants already fixed elsewhere — pipe-as-start-of-line
anchor (`parser-greedy-regex`), missing sanitization chains
(`parser-sanitization-gaps`), the sanitize_text trailing-newline bug
(`sanitize-text-newline-bug`), QuoteBlock over-sanitization
(`quoteblock-over-sanitization`), and greedy regex patterns
(`parser-greedy-regex`).

- **CRLF handling is deferred to this issue.** Other bug fixes that
  touch line-splitting logic (e.g., `sanitize-text-newline-bug`
  switching from `splitlines()` to `split('\n')`) consciously do not
  account for CRLF. When CRLF support is implemented here, all
  line-splitting call sites must be revisited project-wide, including
  `sanitize_text()` in `tiredize/markdown/utils.py`.

- **Delivered one element type at a time.** The full set is too large to
  scope, review, or land as a single change. Each element becomes its
  own issue tagged `gfm-parity` when scheduled; this issue is the
  register. Grouping is by tag, not hierarchy, per the issue-file
  standard.

### Cross-cutting themes

Roughly eighteen of the fifty skips share a root cause across element
boundaries. Per-element is a sound unit of *delivery* but a poor unit of
*design* for these: split naively, CRLF gets solved three times, likely
three different ways. Whoever takes the second element in a theme should
inherit the first one's decision rather than re-litigate it.

| Theme | Element types affected |
|-------|------------------------|
| CRLF line endings | CodeBlock, FrontMatter, Table |
| Single-quote titles | InlineLink, InlineImage, ReferenceDefinition |
| Angle-bracket URLs | InlineLink, InlineImage, ReferenceDefinition |
| `]` breaking a match | InlineImage, ReferenceDefinition, LinkReference, ImageReference |
| Escaped quote in title | InlineLink, InlineImage |
| Leading whitespace / indentation | CodeBlock, QuoteBlock, ReferenceDefinition, FrontMatter, Header |

The link, image, and reference family accounts for 21 of the 50 and
shares title-and-URL parsing throughout. Those elements want sequencing
together, or a single owner.

### Findings

#### CodeBlock (6 skips)

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

#### CodeInline (4 skips)

- Double-backtick inline code (``` `` code `` ```) not matched.
  Pattern only handles single-backtick delimiters.
- Triple-backtick inline code not matched. Same issue.
- Inline code containing a single backtick (multi-backtick wrapper)
  not supported. Would require matching balanced multi-backtick
  delimiters.
- Multiline inline code (`\`foo\nbar\``) not matched.
  Character class `[^\n\`]` excludes newlines.

#### Header (5 skips)

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

#### InlineLink (7 skips)

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

#### BracketLink (2 skips)

- Non-HTTP schemes (`<ftp://example.com>`, `<mailto:user@host>`)
  not matched. Pattern requires `https?://`.
- Email autolinks (`<user@example.com>`) not matched.

#### BareLink (2 skips)

- `www.` prefix without scheme not matched. Pattern requires
  `http[s]?://` or `./` or `\`.
- Trailing punctuation (`https://example.com.`) captured as part of
  URL. GFM strips trailing punctuation from extended autolinks.

Note that the backslash false-positive class is *not* tracked here.
`BareLink` is a deliberate superset of GFM — GFM never autolinks
relative or Windows paths — so that bug lives in tiredize-specific
territory this issue does not reach. See
`bare-link-backslash-collision`.

#### InlineImage (5 skips)

- Single-quote title not captured (same as InlineLink).
- Angle-bracket URL not matched (same as InlineLink).
- `]` in alt text breaks match (same as InlineLink text).
- Empty URL not matched (same as InlineLink).
- Escaped quote in title truncated (same as InlineLink).

#### ReferenceDefinition (5 skips)

- Single-quote title not captured.
- Angle-bracket URL (`[ref]: <url>`) not matched.
- URL without `#`, `.`, or `/` (`[ref]: example`) rejected by
  pattern `\S*[#\.\/]+\S*`.
- Indented definition (1-3 spaces) not matched.
- `]` in label breaks match.

#### LinkReference (2 skips)

- Collapsed reference (`[text][]`) detected as shortcut reference
  instead. `text` field is None instead of content.
- `]` in reference label breaks match.

#### ImageReference (2 skips)

- Collapsed image reference (`![alt][]`) same issue as LinkReference.
- `]` in reference label breaks match.

#### Table (2 skips)

- Escaped pipes (`\|`) in cells cause over-split. `split("|")`
  does not handle backslash escapes.
- CRLF line endings cause complete match failure.

#### QuoteBlock (3 skips)

- Lazy continuation (`> first\nsecond` as single quote) not matched.
  Only lines starting with `>` are captured.
- Spaced nested quotes (`> > nested`) parsed as depth 1.
  Pattern `[>]+` requires consecutive `>` without spaces.
- Indented block quote (`   > quote`) not matched.

#### FrontMatter (5 skips)

- `...` (three dots) closing delimiter not matched.
- Empty frontmatter (`---\n---\n`) not matched.
- More than 3 dashes (`----`) not matched. `[-]{3}` matches
  exactly 3.
- CRLF line endings cause complete match failure.
- Leading whitespace on delimiter not matched (this is actually
  correct behavior for most implementations).

#### CRLF data quality (not skipped, documented as actual behavior)

Several types match with CRLF input but capture `\r` as content:
- Header titles include trailing `\r`
- QuoteBlock quotes include trailing `\r`
- CodeInline content includes `\r`
- ReferenceDefinition matches succeed (CRLF doesn't break the
  match because `\s*?` absorbs `\r`)

## Open Questions

- What is the priority order across the twelve element types? Which
  variants do real-world documents most commonly use? TRR source
  material is the obvious evidence base.
- Should CRLF handling be lifted out as its own cross-cutting issue
  rather than solved inside CodeBlock, FrontMatter, and Table
  separately? The same question applies to the title-and-URL themes
  shared across the link, image, and reference family.

## Comments

### 2026-06-15T00:00:00+00:00

Author: program-manager

    Migrated to the v2 issue format during the `.context/` process
    migration. The `parent` field (test-coverage-audit) was dropped —
    v2 groups via tags, not hierarchy. Findings moved under Design
    Decisions; Out of Scope folded in; the v1 Completion Report dropped.

### 2026-09-14T00:00:00+00:00

Author: program-manager

    Restructured into per-element units of work following the PR #44
    review, where the question "which element type covers this
    contributor's bug" could not be answered from the issue as written.

    Skip counts re-derived from `pytest -rs` rather than trusted from
    the issue text. The total was recorded as 52; it is 50. Several
    per-element counts were also wrong: InlineLink 6 to 7,
    ReferenceDefinition 4 to 5, FrontMatter 4 to 5, ImageReference 3 to
    2, BareLink 3 to 2.

    Two Findings entries were stale and have been removed: the
    InlineImage greedy-paren bullet (fixed under `parser-greedy-regex`)
    and the BareLink `../` partial-match bullet (fixed — the pattern now
    orders `../` before `./`). Both were counted as open gaps and are
    not.

    The first Open Question — split or single issue — is resolved and
    moved to Design Decisions.
