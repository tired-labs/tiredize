# Specification: Markdown Parser

## Overview

The markdown parser converts raw markdown text into a tree of typed
dataclass elements. It owns the document model, element extraction,
text sanitization (to prevent false matches across element types), and
position tracking. Located in `tiredize/markdown/`.

## Contracts and Interfaces

### Entry Point

```python
@dataclass(frozen=False)
class Document:
    frontmatter: FrontMatter | None = None
    path: Path | None = None
    sections: list[Section] = field(default_factory=_new_sections)
    string_markdown: str = ""
    string: str = ""

    def load(self, path: Path = Path(), text: str = "") -> None
    def line_col(self, offset: int) -> tuple[int, int]
```

`Document.load()` reads a file (via `path`) or accepts raw text (via
`text`), then calls `_parse()` to populate `sections`, `frontmatter`,
and computed fields. `line_col()` converts a character offset to a
`(line, column)` tuple where line is 1-based and column is 0-based.

### Shared Types

```python
@dataclass(frozen=True)
class Position:
    offset: int
    length: int
```

Defined in `tiredize/core_types.py`. All parsed elements carry a
`Position` where `offset` is a character index relative to the
document root (character 0 of the original file content).

### Element Type Pattern

Every markdown element type follows this pattern:

- A frozen or mutable dataclass with a `position: Position` field.
- A class-level regex constant (`RE_*`) using `re.VERBOSE` syntax.
- A `@staticmethod extract(text: str, base_offset: int = 0) -> list[T]`
  method that finds all instances in the given text.
- A `@staticmethod sanitize(text: str) -> str` method that replaces
  matched regions with whitespace, preserving character offsets for
  downstream extractors.

The `base_offset` parameter threads position tracking through nested
extraction calls so that offsets in child elements are relative to the
document root, not to the parent's text slice.

### Utility Functions

```python
# tiredize/markdown/utils.py
def search_all_re(pattern: str, string: str) -> list[re.Match[str]]
def get_position_from_match(
    match: re.Match[str], text: str) -> tuple[int, int, int]
def sanitize_text(pattern: str, text: str) -> str
```

`search_all_re` wraps `re.finditer` with `re.VERBOSE`. `sanitize_text`
replaces pattern matches with whitespace to preserve offsets. It splits
on `\n` (not `splitlines()`) to ensure trailing newlines in matched
regions are preserved in the output. The output length must always
equal the input length. `get_position_from_match` returns
`(line_number, column_offset, match_length)` for a regex match.

## File Layout

```
tiredize/markdown/
├── __init__.py
├── utils.py            search_all_re, get_position_from_match,
│                       sanitize_text
└── types/
    ├── __init__.py
    ├── code.py          CodeBlock, CodeInline
    ├── document.py      Document
    ├── frontmatter.py   FrontMatter
    ├── header.py        Header (+ slugify_header)
    ├── image.py         InlineImage
    ├── link.py          InlineLink, BracketLink, BareLink
    ├── list.py          List
    ├── quoteblock.py    QuoteBlock
    ├── reference.py     LinkReference, ImageReference,
    │                    ReferenceDefinition
    ├── section.py       Section (tree builder, extraction
    │                    orchestrator)
    └── table.py         Table
```

## Regex Constants

Regex patterns are class-level constants prefixed with `RE_` (e.g.,
`RE_HEADER`, `RE_CODEBLOCK`) and use `re.VERBOSE` syntax. This allows
inline comments and whitespace for readability.

### Start-of-Line Anchor

Block-level elements (CodeBlock, Header, QuoteBlock,
ReferenceDefinition) use `(?:(?<=\n)|(?:^))` as a zero-width
start-of-line anchor. This matches at the start of the string or
immediately after a newline, but not after `|` or other characters.
The previous anchor `(?<![^|\n])` used a negated character class
that included `|`, causing it to accept `|` as a valid predecessor
and producing false positive matches inside table cells.

### URL Pattern in Inline Links and Images

`InlineLink` and `InlineImage` use `[^\s)]+` to capture URLs. The
`)` exclusion prevents the pattern from consuming past the closing
parenthesis into adjacent syntax. URLs containing literal `)` (e.g.,
balanced parentheses in Wikipedia URLs) are not supported — tracked
in `gfm-parity.md`.

### BareLink Relative Path Matching

`BareLink.RE_URL` matches `../` as an explicit alternative before
`./`, preventing `./` from false-matching inside `../` paths.
Backslash paths (`\`) are also supported for Windows-style paths.

### Pattern Reference

Each pattern is shown in `re.VERBOSE` form with named capture groups
and component descriptions.

#### `CodeBlock.RE_CODEBLOCK` (code.py)

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<delimiter>``[`]+)   # Opening fence: 3+ backticks
(?P<language>.*)        # Optional language identifier
\n                      # Newline after opening fence
(?P<code>[\s\S]*?)      # Code content (lazy, spans newlines)
\n                      # Newline before closing fence
\1                      # Closing fence: must match opening backtick count
```

The closing fence uses backreference `\1` to ensure the delimiter
length matches. `[\s\S]*?` is used instead of `.*?` because `.`
does not match newlines. The lazy quantifier prevents consuming
past the first matching closing fence.

#### `CodeInline.RE_CODE_INLINE` (code.py)

```
`                       # Opening backtick
(?P<code>[^\n`]+)       # Content: any chars except backtick or newline
`                       # Closing backtick
```

Does not support multi-backtick inline code (e.g., ` `` code `` `).
The `[^\n`]` exclusion prevents matching across lines. Tracked in
`gfm-parity.md`.

#### `FrontMatter.RE_FRONT_MATTER_YAML` (frontmatter.py)

```
^                       # Must be at absolute start of string
[-]{3}                  # Opening fence: ---
\n                      # Newline
(?P<yaml>[\s\S]*?)      # YAML content (lazy, spans newlines)
\n                      # Newline
[-]{3}                  # Closing fence: ---
\n                      # Trailing newline
```

Anchored to `^` (start of string), not start-of-line. FrontMatter
is always the first thing in a document. The closing `---\n`
requires a trailing newline, so `---` at end-of-file without a
newline will not match.

#### `Header.RE_HEADER` (header.py)

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<hashes>\#{1,6})     # 1-6 hash characters (heading level)
\s+                     # Mandatory whitespace after hashes
(?P<title>[^\n]+)       # Title: rest of line
```

Requires at least one space after `#`. A line like `#no-space`
will not match. The title captures everything to end-of-line
including trailing whitespace and closing `#` characters.

#### `InlineImage.RE_INLINE_IMAGE` (image.py)

```
!\[                     # Opening: exclamation mark + bracket
\s*                     # Optional whitespace
(?P<text>[^]]*?)        # Alt text (lazy, excludes ])
\s*                     # Optional whitespace
\]\(                    # Closing bracket + opening parenthesis
\s*                     # Optional whitespace
(?P<url>[^\s)]+)        # URL: non-whitespace, excludes )
(\s*?\"(?P<title>[^"]*?)\")?  # Optional title in double quotes
\s*\)                   # Closing parenthesis
```

The `[^\s)]+` URL pattern prevents greedy consumption past the
closing `)`. See "URL Pattern in Inline Links and Images" above.

#### `InlineLink.RE_LINK_INLINE` (link.py)

```
(?<!!)                  # Negative lookbehind: not preceded by !
\[\s*                   # Opening bracket + optional whitespace
(?P<text>[^]]*?)        # Link text (lazy, excludes ])
\s*                     # Optional whitespace
\]\(                    # Closing bracket + opening parenthesis
\s*                     # Optional whitespace
(?P<url>[^\s)]+)        # URL: non-whitespace, excludes )
(\s*?\"(?P<title>[^"]*?)\")?  # Optional title in double quotes
\s*\)                   # Closing parenthesis
```

The `(?<!!)` lookbehind prevents matching `![text](url)` as a
link (images start with `!`). Otherwise identical to InlineImage.

#### `BracketLink.RE_LINK_BRACKET` (link.py)

```
<                       # Opening angle bracket
(?P<url>https?:\/\/\S+) # URL: must start with http:// or https://
>                       # Closing angle bracket
```

Only matches absolute HTTP/HTTPS URLs. Relative paths and other
protocols (ftp, mailto) are not supported.

#### `BareLink.RE_URL` (link.py)

```
(?P<url>
    (http[s]?:\/\/      # Absolute URL: http:// or https://
    |(\.\.\/)           # Parent-relative path: ../
    |(\.\/|\\)          # Current-relative path: ./ or \ (Windows)
    )\S+                # Rest of URL: any non-whitespace
)
```

The `../` alternative appears before `./` to prevent `./` from
false-matching at position 1 inside `../` paths. See "BareLink
Relative Path Matching" above. `\S+` is used here (not `[^\s)]+`)
because bare links have no closing delimiter to consume past.

#### `ReferenceDefinition.RE_REFERENCE_DEFINITION` (reference.py)

```
(?:(?<=\n)|(?:^))\[     # Start-of-line anchor + opening bracket
(?P<text>[^]]*?)        # Label text (lazy, excludes ])
\]:\s+                  # Closing bracket + colon + whitespace
(?P<url>\S*[#\.\/]+\S*) # URL: must contain #, ., or /
\s*?                    # Optional whitespace
("(?P<title>[^"]*)")?   # Optional title in double quotes
(?=\n|$)                # Lookahead: must end at newline or EOF
```

The URL pattern `\S*[#\.\/]+\S*` requires at least one `#`, `.`,
or `/` character. This prevents plain words from matching as URLs
but also means URLs without these characters are rejected (tracked
in `gfm-parity.md`). The end-of-line lookahead ensures definitions
don't consume content on the same line.

#### `LinkReference.RE_LINK_REFERENCE` (reference.py)

```
(?<!(!|\]))\[           # Not preceded by ! or ] + opening bracket
(\s*(?P<text>[^]]*?)    # Optional: link text (lazy, excludes ])
\s*\]\[)?               # Optional: closing bracket + opening bracket
\s*                     # Optional whitespace
(?P<reference>[^\]]+)   # Reference label (excludes ])
\s*                     # Optional whitespace
\](?!:)                 # Closing bracket, not followed by :
(?!\()                  # Not followed by ( (excludes inline links)
```

Matches both full references `[text][ref]` and shortcut
references `[ref]`. The `(?<!(!|\]))` lookbehind prevents matching
image references (`![alt][ref]`) and consecutive bracket
sequences. The `(?!:)` lookahead prevents matching reference
definitions `[ref]:`. The `(?!\()` lookahead prevents matching
inline links `[text](url)`.

#### `ImageReference.RE_IMAGE_REFERENCE` (reference.py)

```
!\[                     # Opening: exclamation mark + bracket
(\s*(?P<text>[^]]*?)    # Optional: alt text (lazy, excludes ])
\s*\]\[)?               # Optional: closing bracket + opening bracket
\s*                     # Optional whitespace
(?P<reference>[^\]]+)   # Reference label (excludes ])
\s*                     # Optional whitespace
\](?!:)                 # Closing bracket, not followed by :
(?!\()                  # Not followed by ( (excludes inline images)
```

Same structure as LinkReference but anchored by `![` instead of
lookbehind filtering. Matches both full `![alt][ref]` and shortcut
`![ref]` forms.

#### `QuoteBlock.RE_QUOTEBLOCK` (quoteblock.py)

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<depth>[>]+)         # Blockquote depth: one or more >
\s*                     # Optional whitespace after >
(?P<quote>[^\n]*)       # Quote content: rest of line
```

Matches individual blockquote lines. The `extract()` method
merges consecutive lines of the same depth into a single
QuoteBlock element. Multi-level nesting is indicated by the
`depth` field (e.g., `>>` has depth 2).

#### `Table.RE_TABLE` (table.py)

```
(?P<header>             # Header row:
    [|]?                #   Optional leading pipe
    ([^\n|]*[|])*       #   Zero or more cells followed by pipe
    [^\n|]+             #   Final cell (no trailing pipe required)
    [|]?                #   Optional trailing pipe
    \n                  #   Newline
)
(?P<divider>            # Divider row (two alternatives):
    [|][ \t]*:?-+:?[ \t]*       # Alt 1: starts with pipe
    ([|][ \t]*:?-+:?[ \t]*)*    #   more pipe-separated cells
    [|]?\n                       #   optional trailing pipe + newline
    |                            # -- OR --
    [ \t]*:?-+:?[ \t]*          # Alt 2: starts without pipe
    ([|][ \t]*:?-+:?[ \t]*)+    #   one or more pipe-separated cells
    [|]?\n                       #   optional trailing pipe + newline
)
(?P<rows>               # Data rows:
    ([^\n]*\|[^\n]*     #   Each row must contain at least one pipe
    (\n|$))*            #   Terminated by newline or end-of-string
)
```

The divider uses two alternatives to ensure at least one pipe
appears in the repeating group, preventing catastrophic
backtracking. See "Table divider regex rewrite" in Design
Decisions. Data rows require `|` on each line — a line without
`|` terminates the table, preventing the rows pattern from
consuming non-table content.

## Sanitize Chain

Extractors call `sanitize()` on higher-precedence types before running
their own regex to avoid false matches. For example, link extraction
sanitizes out code blocks and inline code first because a URL inside a
fenced code block is not a rendered link.

The precedence order was determined empirically by testing against
GitHub's markdown rendering behavior. It is not yet exhaustive -- edge
cases remain and the ordering should be validated with unit tests
against GitHub-Flavored Markdown (GFM) rendering rules.

### Per-Extractor Sanitization Chains

Each extractor should sanitize internally before matching, independent
of calling context, ensuring correct results whether called from
`Section._extract()`, standalone scripts, or a future API.
`Table.extract()` is the sole exception — it currently relies on
`Section._extract()` to pass CodeBlock-sanitized input. This is
tracked in `table-internal-sanitization.md`.

| Extractor             | Sanitizes (in order)                      |
|-----------------------|-------------------------------------------|
| `CodeBlock`           | (none -- highest precedence)              |
| `CodeInline`          | CodeBlock                                 |
| `FrontMatter`         | (none -- extracted before Section parse)  |
| `Header`              | CodeBlock                                 |
| `InlineImage`         | CodeBlock, CodeInline                     |
| `InlineLink`          | CodeBlock, CodeInline, QuoteBlock         |
| `BracketLink`         | CodeBlock, CodeInline, QuoteBlock         |
| `BareLink`            | CodeBlock, CodeInline, QuoteBlock,        |
|                       | InlineImage, BracketLink, InlineLink,     |
|                       | ReferenceDefinition                       |
| `ReferenceDefinition` | CodeBlock                                 |
| `LinkReference`       | CodeBlock, CodeInline                     |
| `ImageReference`      | CodeBlock, CodeInline                     |
| `QuoteBlock`          | CodeBlock                                 |
| `List`                | (none)                                    |
| `Table`               | (none, but `Section._extract` passes      |
|                       | CodeBlock-sanitized text)                 |

**Design principle:** The chain order follows GFM rendering
precedence. Code constructs have highest precedence (content inside
code is never interpreted as other elements). Link extractors
sanitize QuoteBlock because the `>` prefix can interfere with link
pattern matching. BareLink has the deepest chain because bare URLs
are the most ambiguous pattern and must exclude all other link types.

**Known gaps:**
- QuoteBlock sanitization blanks entire line content instead of
  stripping `> ` prefixes, causing link extractors to miss valid
  links inside blockquotes. Tracked in
  `quoteblock-over-sanitization.md`.
- InlineImage does not sanitize QuoteBlock. This is intentional --
  GitHub renders images inside blockquotes, so they are valid
  content. When the QuoteBlock over-sanitization bug is fixed,
  this decision should be revisited.

### Section._extract() Orchestration

`Section._extract()` passes raw `string` to all extractors,
relying on each to sanitize internally. The exception is
`Table.extract()`, which receives `CodeBlock.sanitize(string)`.

The `string_safe` field stored on each `Section` is
`CodeInline.sanitize(CodeBlock.sanitize(string))`. It is not passed
to any extractor; it is stored for downstream consumers (e.g., linter
rules that need code-free text).

## Design Decisions

- **Table divider regex rewrite:** The original `RE_TABLE` divider
  pattern used an optional pipe `[|]?` inside a repeating group
  followed by a mandatory pipe, causing catastrophic backtracking
  (exponential O(2^n) time) on long dash sequences without pipes.
  Rewritten as two alternatives, each with mandatory pipes inside
  the repeating group, eliminating backtracking. See issue
  `parser-robustness.md` for full details.

- **Table extraction receives sanitized input:** `Table.extract()` in
  `Section._extract()` receives `CodeBlock.sanitize(string)` rather
  than raw text, preventing both false table matches inside code
  fences and triggering the backtracking vulnerability above.
