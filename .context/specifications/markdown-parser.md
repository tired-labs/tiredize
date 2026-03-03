# Specification: Markdown Parser

## Overview

The markdown parser converts raw markdown text into a tree of typed
dataclass elements. It owns the document model, element extraction,
text sanitization (to prevent false matches across element types), and
position tracking. Located in `tiredize/markdown/`.

Each element type has its own specification file with regex patterns,
dataclass fields, sanitization chains, and GFM compliance assessment.
This hub document covers shared concepts, cross-cutting architecture,
and the file layout.

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

### Shared Regex Patterns

#### Start-of-Line Anchor

Block-level elements (CodeBlock, Header, QuoteBlock,
ReferenceDefinition) use `(?:(?<=\n)|(?:^))` as a zero-width
start-of-line anchor. This matches at the start of the string or
immediately after a newline, but not after `|` or other characters.
The previous anchor `(?<![^|\n])` used a negated character class
that included `|`, causing it to accept `|` as a valid predecessor
and producing false positive matches inside table cells.

#### URL Pattern in Inline Links and Images

`InlineLink` and `InlineImage` use `[^\s)]+` to capture URLs. The
`)` exclusion prevents the pattern from consuming past the closing
parenthesis into adjacent syntax. URLs containing literal `)` (e.g.,
balanced parentheses in Wikipedia URLs) are not supported — tracked
in `gfm-parity.md`.

#### BareLink Relative Path Matching

`BareLink.RE_URL` matches `../` as an explicit alternative before
`./`, preventing `./` from false-matching inside `../` paths.
Backslash paths (`\`) are also supported for Windows-style paths.

## Element Type Specifications

Per-type specification files follow a consistent template with
dataclass fields, regex pattern, sanitization chain, GFM compliance
assessment, and naming mappings.

### Block-Level Elements

- [`markdown-type-codeblock.md`](markdown-type-codeblock.md) — CodeBlock (fenced code blocks)
- [`markdown-type-codeinline.md`](markdown-type-codeinline.md) — CodeInline (code spans)
- [`markdown-type-header.md`](markdown-type-header.md) — Header (ATX headings)
- [`markdown-type-quoteblock.md`](markdown-type-quoteblock.md) — QuoteBlock (block quotes)
- [`markdown-type-table.md`](markdown-type-table.md) — Table (GFM tables)
- [`markdown-type-list.md`](markdown-type-list.md) — List (stub — not implemented)

### Inline Elements

- [`markdown-type-inlineimage.md`](markdown-type-inlineimage.md) — InlineImage (images)
- [`markdown-type-inlinelink.md`](markdown-type-inlinelink.md) — InlineLink (links)
- [`markdown-type-bracketlink.md`](markdown-type-bracketlink.md) — BracketLink (autolinks)
- [`markdown-type-barelink.md`](markdown-type-barelink.md) — BareLink (extended autolinks)

### Reference Elements

- [`markdown-type-referencedefinition.md`](markdown-type-referencedefinition.md) — ReferenceDefinition (link reference definitions)
- [`markdown-type-linkreference.md`](markdown-type-linkreference.md) — LinkReference (reference links)
- [`markdown-type-imagereference.md`](markdown-type-imagereference.md) — ImageReference (reference images)

### Structural Elements

- [`markdown-type-frontmatter.md`](markdown-type-frontmatter.md) — FrontMatter (YAML frontmatter)
- [`markdown-type-document.md`](markdown-type-document.md) — Document (top-level container)
- [`markdown-type-section.md`](markdown-type-section.md) — Section (tree builder and extraction orchestrator)

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

## Sanitization Architecture

Extractors call `sanitize()` on higher-precedence types before running
their own regex to avoid false matches. For example, link extraction
sanitizes out code blocks and inline code first because a URL inside a
fenced code block is not a rendered link.

The precedence order was determined empirically by testing against
GitHub's markdown rendering behavior. It is not yet exhaustive — edge
cases remain and the ordering should be validated with unit tests
against GitHub-Flavored Markdown (GFM) rendering rules.

### Per-Extractor Sanitization Chains

Each extractor sanitizes internally before matching, independent of
calling context, ensuring correct results whether called from
`Section._extract()`, standalone scripts, or a future API.

| Extractor             | Sanitizes (in order)                      |
|-----------------------|-------------------------------------------|
| `CodeBlock`           | (none — highest precedence)               |
| `CodeInline`          | CodeBlock                                 |
| `FrontMatter`         | (none — extracted before Section parse)   |
| `Header`              | CodeBlock                                 |
| `InlineImage`         | CodeBlock, CodeInline                     |
| `InlineLink`          | CodeBlock, CodeInline                     |
| `BracketLink`         | CodeBlock, CodeInline                     |
| `BareLink`            | CodeBlock, CodeInline, InlineImage,       |
|                       | BracketLink, InlineLink,                  |
|                       | ReferenceDefinition                       |
| `ReferenceDefinition` | CodeBlock                                 |
| `LinkReference`       | CodeBlock, CodeInline                     |
| `ImageReference`      | CodeBlock, CodeInline                     |
| `QuoteBlock`          | CodeBlock                                 |
| `List`                | (none)                                    |
| `Table`               | CodeBlock                                 |

**Design principle:** The chain order follows GFM rendering
precedence. Code constructs have highest precedence (content inside
code is never interpreted as other elements). BareLink has the
deepest chain because bare URLs are the most ambiguous pattern and
must exclude all other link types.

**QuoteBlock and link extractors:** Link extractors do not sanitize
QuoteBlock. Per GFM, blockquote content is real markdown — links
inside blockquotes are valid and should be extracted. The `>` prefix
does not interfere with any link regex pattern (none use
start-of-line anchors or characters that conflict with `>`). See
issue `quoteblock-over-sanitization.md`.

### Section._extract() Orchestration

`Section._extract()` passes raw `string` to all extractors,
relying on each to sanitize internally.

The `string_safe` field stored on each `Section` is
`CodeInline.sanitize(CodeBlock.sanitize(string))`. It is not passed
to any extractor; it is stored for downstream consumers (e.g., linter
rules that need code-free text).

## Unimplemented GFM Features

The following GFM features have no implementation in the parser.
Each is tracked as a sub-issue of `gfm-parity.md`:

- **Thematic breaks** (GFM 4.1) — Horizontal rules (`---`, `***`,
  `___`). See `gfm-thematic-break.md`.
- **Setext headings** (GFM 4.3) — Underline-style headings. See
  `gfm-setext-heading.md`.
- **Indented code blocks** (GFM 4.4) — 4-space indented code. See
  `gfm-indented-code-block.md`.
- **Emphasis and strong emphasis** (GFM 6.2) — `*em*`, `**strong**`,
  `_em_`, `__strong__`. See `gfm-emphasis.md`.
- **Strikethrough** (GFM extension) — `~~text~~`. See
  `gfm-strikethrough.md`.
- **Task list items** (GFM extension) — `- [ ] task`. See
  `gfm-task-list.md`.
- **Hard line breaks** (GFM 6.7) — Trailing spaces or `\` at EOL.
  See `gfm-hard-line-break.md`.
- **HTML blocks** (GFM 4.6) — Raw HTML blocks. See
  `gfm-html-block.md`.

## Design Decisions

- **Table divider regex rewrite:** The original `RE_TABLE` divider
  pattern used an optional pipe `[|]?` inside a repeating group
  followed by a mandatory pipe, causing catastrophic backtracking
  (exponential O(2^n) time) on long dash sequences without pipes.
  Rewritten as two alternatives, each with mandatory pipes inside
  the repeating group, eliminating backtracking. See issue
  `parser-robustness.md` for full details.

- **Table extraction sanitizes internally:** `Table.extract()` calls
  `CodeBlock.sanitize()` on its input before matching, consistent with
  all other extractors. This prevents false table matches inside code
  fences. Previously, sanitization was handled externally by
  `Section._extract()` — see issue `table-internal-sanitization.md`.
