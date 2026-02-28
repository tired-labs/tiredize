Status: active
Parent: test-coverage-audit.md

# Test Coverage: Markdown Element Types

## Summary

Write comprehensive test suites for markdown element types that have
zero or insufficient test coverage. For every element type, test not
only basic extraction and sanitization but also cross-type interactions
-- what happens when one element type appears inside another? These
interaction tests document the parser's actual behavior and catch false
positives caused by missing or incomplete sanitization chains. Part of
the test coverage audit (`test-coverage-audit.md`).

## Acceptance Criteria

### New test files (zero coverage today)

- [x] `tests/markdown/types/test_link.py` -- BareLink, BracketLink,
      InlineLink (see test matrix below)
- [x] `tests/markdown/types/test_reference.py` -- ReferenceDefinition,
      LinkReference, ImageReference (see test matrix below)
- [x] `tests/markdown/types/test_list.py` -- stub behavior tests
      confirming List.extract() returns empty list (not yet implemented)

### Sanitize method coverage (no direct tests today)

- [x] Direct sanitize() tests for: Header, FrontMatter, Table,
      BareLink, BracketLink, InlineLink, ReferenceDefinition,
      LinkReference, ImageReference. Each test verifies matched regions
      are replaced with whitespace and total string length is preserved.

### Edge case coverage (partially tested today)

- [x] FrontMatter.extract() with malformed YAML (lines 52-53:
      exception handler path)
- [x] Header.slugify_header() with empty title (line 96: fallback to
      "section")
- [x] Section.extract() with no headers in text (lines 51-60: creates
      single section with full text)
- [x] Document.line_col() with negative offset and offset beyond
      document length (lines 44, 47: bounds clamping)

### Cross-type interaction tests

For each element type being tested, verify behavior when it appears
inside every other element type that could contain or mimic it. These
tests document the parser's actual behavior. If behavior differs from
what GitHub-Flavored Markdown renders, note it in a comment but do not
fix the parser (sanitization chain fixes belong in
`parser-sanitization-audit.md`).

- [x] **Links inside code blocks** -- InlineLink, BracketLink,
      BareLink, LinkReference inside a fenced code block. Verify links
      that do internal sanitization correctly exclude these. Verify
      links that don't sanitize (if any) produce false positives and
      document the behavior.
- [x] **Links inside inline code** -- `[text](url)`, `<url>`,
      `http://...`, `[text][ref]` inside backtick spans. Same
      verification as above.
- [x] **Links inside quote blocks** -- Links inside `> ` prefixed
      lines. In rendered markdown these ARE real links. Verify whether
      the parser extracts them. Document behavior either way.
- [x] **Links inside tables** -- Links in table cells. In rendered
      markdown these ARE real links. Verify extraction behavior.
- [x] **Images vs links** -- Verify `![alt](url)` is NOT extracted as
      an InlineLink (negative lookbehind `(?<!!)` must work). Verify
      `[text](url)` is NOT extracted as an InlineImage. Test adjacent
      placement: `![img](a.png)[link](b.html)`.
- [x] **Images inside code blocks** -- `![alt](url)` inside fenced
      code block. InlineImage does NO sanitization; verify whether it
      produces a false positive.
- [x] **Images inside inline code** -- Same test with backtick spans.
      InlineImage does no sanitization; verify behavior.
- [x] **Images inside quote blocks** -- `![alt](url)` inside `> `
      lines. InlineImage does no sanitization; verify behavior.
- [x] **References inside code blocks** -- `[text][ref]` and
      `[ref]: url` inside fenced code blocks. ReferenceDefinition and
      LinkReference only sanitize CodeBlock; verify this works.
- [x] **References inside inline code** -- Same test with backtick
      spans. These extractors do NOT sanitize CodeInline; verify
      whether false positives occur.
- [x] **References inside quote blocks** -- Reference definitions and
      link references inside `> ` lines. These extractors do NOT
      sanitize QuoteBlock; verify behavior.
- [x] **Image references inside code blocks** -- `![alt][ref]` inside
      fenced code blocks. ImageReference only sanitizes CodeBlock;
      verify this works.
- [x] **Image references inside inline code** -- Same test with
      backtick spans. ImageReference does NOT sanitize CodeInline;
      verify behavior.
- [x] **Nested code** -- Inline code inside a fenced code block.
      Fenced code block inside inline backticks (edge case). Verify
      neither produces false matches.
- [x] **FrontMatter containing element-like syntax** -- YAML
      frontmatter with values that look like links, images, code
      blocks, or headers. Verify FrontMatter.extract() handles these
      and other extractors don't match inside frontmatter.

### Review existing tests for completeness

- [x] Review `test_codeblock.py` -- verify CodeBlock extract and
      sanitize cover edge cases (empty input, nested backticks,
      unclosed fence, language tag variations). Add missing tests.
- [x] Review `test_codeinline.py` -- verify CodeInline extract and
      sanitize cover edge cases (empty backticks, adjacent backticks,
      escaped backticks). Add missing tests.
- [x] Review `test_frontmatter.py` -- verify extraction covers all
      paths. Add missing tests beyond the malformed YAML case above.
- [x] Review `test_header.py` -- verify extraction and slugification
      cover edge cases (special characters in titles, duplicate slug
      generation, trailing whitespace). Add missing tests.
- [x] Review `test_image.py` -- verify InlineImage extract covers
      edge cases (empty alt text, URLs with spaces, missing closing
      paren). Add missing tests.
- [x] Review `test_quoteblock.py` -- verify QuoteBlock extract covers
      edge cases (varying depth levels `>>`, `>>>`, empty quote lines,
      adjacent quote blocks). Add missing tests.
- [x] Review `test_section.py` -- verify section tree building covers
      all hierarchy scenarios. Add missing tests.
- [x] Review `test_table.py` -- verify extraction covers edge cases
      (single column, empty cells, tables with only a header row). Add
      missing tests.
- [x] Review `test_document.py` -- verify Document.load() and
      line_col() cover all paths. Add missing tests.
- [x] Review `test_schema.py` -- verify load_schema() and data model
      tests are complete (already at 100% but check for logical gaps).
      Add missing tests.

### Boundary and degenerate inputs

- [x] For every extract() method: empty string, single-character input,
      input that is entirely one match, input with no trailing newline
- [x] For every sanitize() method: empty string, single-character input,
      input where the entire string matches the pattern

### Idempotency

- [x] For every sanitize() method: `sanitize(sanitize(text))` produces
      the same result as `sanitize(text)` and preserves string length.
      Critical because the sanitization chain applies multiple sanitize
      calls sequentially.
- [x] For extract() methods that build state (Section.extract tree
      building): calling extract twice on the same input produces
      identical results

### State mutation

- [x] Section.extract() does not mutate the input text string
- [x] Section._extract() does not corrupt shared state between
      sibling sections during tree building
- [x] Document.load() called twice on the same Document -- verify
      second call cleanly replaces state rather than accumulating

### Unicode and non-ASCII

- [x] Headers with emoji and accented characters -- verify position
      offsets and slugification are correct
- [x] Links with unicode in text and URL -- verify extraction and
      position tracking
- [x] Images with unicode alt text -- verify extraction
- [x] Table cells with non-ASCII content -- verify extraction
- [x] Code blocks containing non-ASCII -- verify sanitize preserves
      correct string length (characters, not bytes)
- [x] FrontMatter with unicode YAML values -- verify extraction

### Syntax variant coverage (regex audit)

For each element type, test all GFM-valid syntax variants against the
actual regex patterns. Tests assert GFM-spec-correct behavior. When
the code does not match the spec, the test is marked with
`@pytest.mark.skip(reason="...")` referencing the tracking issue.
Do not fix regexes in this issue; regex fixes belong in `gfm-parity.md`.

#### CodeBlock

- [x] Tilde-fenced code blocks (`~~~content~~~`) -- not matched.
      Regex only handles backtick fences.
- [x] Closing fence with trailing spaces (`` ``` ``) -- not matched.
      Backreference `\1` requires exact delimiter match.
- [x] Closing fence with MORE backticks than opening -- not matched.
      GFM allows closing fence >= opening length; `\1` demands exact.
- [x] Indented code fences (1-3 spaces before `` ``` ``) -- not
      matched. Start-of-line anchor requires no leading whitespace.
- [x] Empty code block (zero content lines: `` ```\n``` ``) -- not
      matched. Pattern requires `\n` before closing fence but no
      content newline exists.
- [x] Code fence after `|` character -- false positive match. The
      `(?<![^|\n])` anchor treats `|` as valid start-of-line.

#### CodeInline

- [x] Double-backtick inline code (``` `` code `` ```) -- not matched.
      Pattern only handles single-backtick delimiters.
- [x] Triple-backtick inline code -- same issue as double.
- [x] Inline code containing a single backtick (use multi-backtick
      wrapper) -- incorrectly parsed, wrong boundaries.
- [x] Inline code spanning multiple lines (`` `foo\nbar` ``) -- not
      matched. Character class `[^\n`]` excludes newlines.
- [x] CRLF: `\r` not excluded from content -- captured in code field
      when intent is to prevent line-crossing.

#### Header

- [x] Closing hashes (`# Heading #`, `## Heading ##`) -- trailing
      `#` characters captured as part of title text.
- [x] Empty heading (`# ` with only whitespace after hash) -- not
      matched. `[^\n]+` requires at least one content character after
      `\s+` consumes the space.
- [x] Leading spaces (1-3 before `#`: `   # Heading`) -- not matched.
      Start-of-line anchor requires `#` immediately after newline.
- [x] Setext headings (`Heading\n=======`) -- not matched. Parser
      only handles ATX-style. Document as unsupported.
- [x] Header after `|` character -- false positive match via
      `(?<![^|\n])` anchor.
- [x] CRLF: title field contains trailing `\r`.

#### InlineLink

- [x] Title in single quotes (`[t](url 'title')`) -- title not
      captured. Regex only matches double-quoted titles.
- [x] Title in parentheses (`[t](url (title))`) -- title not captured
      and match may break.
- [x] URL in angle brackets (`[t](<url with spaces>)`) -- not matched.
      `\S+` cannot handle spaces.
- [x] Empty URL (`[text]()`) -- not matched. `\S+` requires at least
      one character.
- [x] Link text containing `]` (`[text \] here](url)`) -- broken.
      `[^]]*?` stops at first `]`, no escape handling.
- [x] Nested brackets in link text (`[text [nested]](url)`) -- broken.
      Same `[^]]` issue.
- [x] Title with escaped quote (`"title \" here"`) -- truncated at
      the escaped quote.

#### BracketLink

- [x] Non-HTTP schemes (`<ftp://example.com>`, `<mailto:user@host>`)
      -- not matched. Pattern requires `https?://`.
- [x] Email autolinks (`<user@example.com>`) -- not matched. No scheme
      prefix to match.

#### BareLink

- [x] `www.` prefix without scheme (`www.example.com`) -- not matched.
      Pattern requires `http[s]?://` or `./` or `\`.
- [x] Trailing punctuation consumption (`https://example.com.`) -- the
      period is captured as part of the URL. GFM strips trailing
      punctuation from extended autolinks.
- [x] Relative paths with `../` prefix -- not matched. Only `./` is
      supported.

#### InlineImage

- [x] Title in single quotes (`![a](url 'title')`) -- same as
      InlineLink: title not captured.
- [x] URL in angle brackets (`![a](<url with spaces>)`) -- same as
      InlineLink: not matched.
- [x] Empty URL (`![alt]()`) -- not matched.
- [x] Alt text containing `]` -- broken, same as InlineLink text.
- [x] Title with escaped quote -- truncated, same as InlineLink.

#### ReferenceDefinition

- [x] Title in single quotes (`[ref]: url 'title'`) -- not captured.
- [x] URL in angle brackets (`[ref]: <url>`) -- not matched.
- [x] URL without `#`, `.`, or `/` (`[ref]: example`) -- not matched.
      Pattern `\S*[#\.\/]+\S*` requires these characters.
- [x] Indented definition (1-3 spaces: `   [ref]: url`) -- not
      matched. Start-of-line anchor requires no indentation.
- [x] CRLF: end-of-line lookahead `(?=\n|$)` -- investigated and
      found NOT to fail. `\s*?` absorbs `\r`, then `\n` satisfies
      the lookahead. Prediction was wrong.
- [x] Label containing `]` -- broken, `[^]]*?` stops at first `]`.

#### LinkReference

- [x] Collapsed reference link (`[text][]`) -- detected as shortcut
      reference instead; `text` field is None instead of content.
- [x] Reference label containing `]` -- broken, `[^\]]+` stops early.
- [x] Reference immediately after image (`![img](url)[ref]`) --
      investigated and found NOT rejected. The `[` in `[ref]` is
      preceded by `)`, not `]`, so the lookbehind correctly allows it.
      Prediction was wrong. Test documents actual (correct) behavior.

#### ImageReference

- [x] Dead lookbehind (`(?<!(\]))`) -- always passes because it checks
      whether `!` (the preceding literal) is `]`. Test confirms it
      provides no filtering.
- [x] Collapsed image reference (`![alt][]`) -- same issue as
      LinkReference.
- [x] Reference label containing `]` -- broken, same as LinkReference.

#### Table

- [x] Over-greedy row matching -- `([^\n]+(\n|$))*` consumes non-table
      content after the table. Verify rows capture extends beyond the
      actual table.
- [x] Leading spaces on header row -- not matched. Header pattern has
      no leading whitespace allowance.
- [x] Escaped pipes in cells (`\|`) -- over-split. `split("|")` does
      not handle escapes.
- [x] CRLF: `\r` captured in cell values. Header, divider, and row
      content all retain `\r`.
- [x] False positive: investigated and found NO false positive.
      Permissive header pattern does not match non-table lines
      containing pipes followed by a dash line. Prediction was wrong.

#### QuoteBlock

- [x] Lazy continuation (`> first\nsecond` as single quote) -- not
      matched. Only lines starting with `>` are captured.
- [x] Nested quote with spaces between markers (`> > nested`) --
      incorrectly parsed as depth 1 with `> nested` as content.
      Pattern `[>]+` requires consecutive `>` without spaces.
- [x] Indented block quote (`   > quote`) -- not matched. Start-of-
      line anchor requires no leading whitespace.
- [x] CRLF: `\r` captured in quote content.
- [x] `|` preceding `>` -- false positive via `(?<![^|\n])` anchor.

#### FrontMatter

- [x] Closing delimiter `...` (three dots) -- not matched. Pattern
      requires `---` for both opening and closing.
- [x] Empty frontmatter (`---\n---\n`, no content lines) -- not
      matched. Pattern requires `\n` before closing fence.
- [x] More than 3 dashes (`----` or `-----`) -- not matched. `[-]{3}`
      matches exactly 3.
- [x] CRLF: complete match failure. Pattern uses literal `\n`.
- [x] Leading whitespace on delimiter (`  ---`) -- not matched.

#### Cross-cutting issues (test across all applicable types)

- [x] **CRLF line endings** -- affects all patterns using `\n`.
      CodeBlock, Header, Table, QuoteBlock, and FrontMatter have data
      quality or match failure issues. Test each type with `\r\n` input
      and document actual behavior.
- [x] **Escaped characters** -- no patterns handle backslash escapes
      (`\[`, `\]`, `` \` ``, `\>`). Test that escaped delimiters are
      incorrectly treated as real delimiters and document the behavior.
- [x] **Leading indentation (1-3 spaces)** -- GFM allows this for
      block-level elements. CodeBlock, Header, QuoteBlock, and
      ReferenceDefinition all reject indented input. Test and document.
- [x] **Pipe character as start-of-line** -- the `(?<![^|\n])` anchor
      treats `|` as valid. Test CodeBlock, Header, QuoteBlock, and
      ReferenceDefinition patterns matching content after `|` inside
      table cells. Document whether this is intentional.

### Coverage target

- [x] 99% coverage on all markdown/types/ source files. `section.py`
      line 167 is unreachable: defensive `break` in `_map_subsections`
      for `header.level == 0`, which never occurs because the method is
      only called when headers exist and level-0 headers are synthetic
      placeholders that don't enter the subsection mapping loop.

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Sanitization chain ordering or fixes (covered by
  `parser-sanitization-audit.md`). Do not modify extractor code.
- Regex fixes for BROKEN syntax variants. Fixes belong in
  `gfm-parity.md`.
- Implementing unsupported GFM variants (tracked by `gfm-parity.md`).
- List.extract() implementation (it is a stub; only stub behavior
  tests required here)
- Writing new tests for `tiredize/markdown/utils.py` (covered by
  `test-coverage-markdown-utils.md`)
- get_position_from_match() dead code (covered by
  `dead-code-cleanup.md`)

### Unsupported GFM variants (planned, not yet implemented)

The following GFM features are not yet handled by the parser. Support
is tracked by `gfm-parity.md`. No tests required in this issue, but
document in test files as known limitations when encountered:

- Indented code blocks (4-space/1-tab without fences)
- Unclosed code fences (GFM extends to end of document)
- HTML `<code>` elements
- Setext headings (`Heading\n=======`)
- GFM extended autolinks (`www.example.com` without scheme)
- Non-HTTP URI schemes (`ftp://`, `mailto:`, `ssh://`)
- TOML/JSON front matter
- Lazy continuation in block quotes
- Multi-line reference definitions (title on next line)

## Design Decisions

- Tests assert specification-correct behavior (GFM spec), not current
  code behavior. When a test fails because the code is broken, the test
  is marked with `@pytest.mark.skip(reason="...")` referencing the issue
  that tracks the fix. The skip is removed when the fix lands.

- Cross-type interaction tests assert what SHOULD happen per GFM spec.
  When the parser produces a false positive due to missing sanitization,
  the test asserts the correct (no false positive) behavior and is
  skipped with an issue reference if the code is broken. The
  sanitization audit issue removes the skip when the fix lands.

- Syntax variant tests assert GFM-spec-correct behavior. When the parser
  does not match a valid GFM variant or produces wrong results, the test
  asserts what correct behavior would be and is skipped with a reference
  to `gfm-parity.md`. Regex fixes belong in that issue, not this test
  coverage work.

## Open Questions
