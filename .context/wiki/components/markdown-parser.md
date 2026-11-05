# Markdown Parser

## Overview

The markdown parser turns raw markdown text into a document of typed
dataclass elements. It owns the document model, element extraction,
sanitization (blanking higher-precedence elements so one element is
not mistaken for another) and position tracking. It lives in
`tiredize/markdown/`.

The parser decides *what* a document contains; it never judges whether
an element is acceptable. Whether a link resolves, a line is too long or
an element is disallowed belongs to the [linter
engine](./linter-engine.md), which reads the `Section` fields this
component fills in, and section structure belongs to the [markdown
schema validator](./markdown-schema-validator.md). The two autolink
elements follow the GFM specification text exactly; their rules are on
[autolinks](./autolinks.md). The other elements are regex-based and
match only part of GFM.

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

`Document.load()` reads a UTF-8 file (via `path`) or takes raw text (via
`text`), then parses it and returns `None`. It raises `ValueError`
with the message `Provide either 'path' or 'text', not both.` when
given both, and `Provide either 'path' or 'text'.` when given neither.
An empty `text` counts as not given, so empty text cannot be loaded
this way, while an empty file loads as one empty section. `Path(".")`
equals the default `Path()` and also counts as not given. A path that
is not a regular file (missing, or a directory) raises
`FileNotFoundError` with the message `Path does not exist: <path>`,
and a file that is not valid UTF-8 raises `UnicodeDecodeError`.

A file is read in text mode with universal newlines, so `\r\n` and a
lone `\r` become `\n` before parsing; text passed as `text` is parsed
exactly as given. `string` holds the whole text as parsed, and every
position refers to it. `path` is set only by a path load and is kept
by a later `load(text=...)` on the same object.

`line_col()` converts a character offset in `string` to a
`(line, column)` pair, line 1-based and column 0-based, counting
characters. An offset below 0 is treated as 0 and one past the end as
the end, so it never raises; before any `load()` it returns `(1, 0)`.

### Document Model

Parsing runs in this order:

1. **Frontmatter.** A YAML block at the very start of the document (see
   `RE_FRONT_MATTER_YAML`) becomes `frontmatter`. Its `content` is
   whatever `yaml.safe_load` returns: usually a mapping, but `None` for
   a block holding only blank lines and a list or scalar when the YAML
   is one. A block whose YAML does not parse yields no frontmatter at
   all: the block is then treated as markdown, and no error is raised.
2. **Markdown.** The rest of the text becomes `string_markdown`. It
   starts one character after the frontmatter's closing `---` line
   ending, so the first character after the frontmatter is skipped: a
   heading on the very next line loses its `#` and is not a heading,
   and the first section's `position` starts one character after the
   frontmatter. Element positions are unaffected and still index
   `string`. A blank line after the frontmatter avoids the problem,
   since the skipped character is then the blank line's newline.
3. **Sections.** Each heading starts a `Section` that runs to the next
   heading of any level: its `string` and `position` cover the heading
   line through the character before the next heading (or the end).
   `sections` lists every section in document order, flat. A section's
   `subsections` are the later sections of a deeper level, up to the
   next section of the same or a higher level, leaving out any section
   already inside an earlier subsection. The levels need not be
   consecutive: in `# 1`, `### 3`, `## 2`, both `### 3` and `## 2` are
   subsections of `# 1`. A document with no heading is one section
   whose header has level 0, an empty title and slug `#section`; it
   has no subsections. When a document has headings, text before the
   first heading belongs to no section, so no element there is
   extracted.
4. **Elements.** Each section's elements are extracted from its own text
   (see Section Fields).
5. **Slugs.** Each header's anchor slug is computed across the whole
   document, so repeated titles get suffixes (see
   `Header.slugify_header`). This overwrites the per-section slug
   `Section.extract()` left on each header.

### Section Fields

```python
# tiredize/markdown/types/section.py
@dataclass(frozen=False)
class Section:
    autolinks: list[Autolink]
    autolinks_extended: list[ExtendedAutolink]
    code_block: list[CodeBlock]
    code_inline: list[CodeInline]
    header: Header
    images_inline: list[InlineImage]
    images_reference: list[ImageReference]
    links_inline: list[InlineLink]
    links_reference: list[LinkReference]
    lists: list[List]
    position: Position
    quoteblocks: list[QuoteBlock]
    reference_definitions: list[ReferenceDefinition]
    string: str
    string_safe: str
    subsections: list[Section]
    tables: list[Table]
```

`lists` is always empty: `List.extract()` is a stub, and lists are not
parsed. Every other field is filled by its element's `extract()`.

```python
@staticmethod
def extract(text: str, base_offset: int = 0) -> list[Section]
```

`Section.extract()` builds the sections and their subsections from
markdown text whose character 0 is at `base_offset`. Called on its own,
it leaves the level-0 header's slug as an empty string, and each
header's slug is computed from its own section only, so repeated titles
are not suffixed; `Document` assigns the document-wide slugs.

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

Every markdown element type except `List` (a stub with no position,
pattern or `sanitize()`) follows this pattern:

- A mutable dataclass (`frozen=False`) with a `position: Position`
  field.
- A class-level regex constant (`RE_*`) using `re.VERBOSE` syntax.
- A `@staticmethod extract(text: str, base_offset: int = 0) -> list[T]`
  method that finds all instances in the given text.
  `FrontMatter.extract()` is the exception: it returns one
  `FrontMatter` or `None`.
- A `@staticmethod sanitize(text: str) -> str` method that replaces
  matched regions with whitespace, preserving character offsets for
  downstream extractors.

The `base_offset` parameter threads position tracking through nested
extraction calls so that offsets in child elements are relative to the
document root, not to the parent's text slice.

### Element Fields

Every element's `string` is the full matched source text and its
`position` covers exactly that text. The autolink fields are on
[autolinks](./autolinks.md).

```python
# code.py
class CodeBlock:      code: str; delimiter: str; language: str
                      position: Position; string: str
class CodeInline:     code: str; position: Position; string: str
# frontmatter.py
class FrontMatter:    content: dict[Any, Any]; position: Position
                      string: str
# header.py
class Header:         level: int; position: Position; slug: str
                      string: str; title: str
# image.py
class InlineImage:    text: str; position: Position; string: str
                      title: str | None; url: str
# link.py
class InlineLink:     position: Position; string: str; title: str
                      url: str
# list.py
class List:           end: int; items: list[str]; match: str
                      start: int; sublists: list[List]
# quoteblock.py
class QuoteBlock:     depth: int; position: Position; quote: str
                      string: str
# reference.py
class ReferenceDefinition: position: Position; string: str; text: str
                      title: str; url: str
class LinkReference:  position: Position; reference: str; string: str
                      text: str | None
class ImageReference: position: Position; reference: str; string: str
                      text: str | None
# table.py
class Table:          divider: list[str]; header: list[str]
                      position: Position; rows: list[list[str]]
                      string: str
```

- **CodeBlock.** `code` is the text between the fence lines, without
  their newlines. `delimiter` is the opening backtick run. `language`
  is the whole info string after the opening fence (`py title=x`
  stays whole), or an empty string.
- **CodeInline.** `code` is the text between the backticks.
- **FrontMatter.** `content` is the parsed YAML, which despite the
  annotation can be `None`, a list or a scalar (see Document Model).
  `string` includes both `---` lines and the final newline.
- **Header.** `level` is the number of `#`. `title` is the rest of the
  line, trailing whitespace and closing `#` included. `string` and
  `position` cover the heading line without its newline. `slug` is the
  anchor (see `Header.slugify_header`).
- **InlineImage and InlineLink.** `url` is the destination and `title`
  the double-quoted title, or `None` when there is none (although
  `InlineLink.title` is annotated `str`). `InlineImage.text` is the alt
  text with surrounding whitespace removed. `InlineLink` has no field
  for the link text.
- **QuoteBlock.** `depth` is the number of adjacent `>` characters.
  `quote` is the content after the `>` run and following whitespace;
  merged lines are joined with `\n`.
- **ReferenceDefinition.** `text` is the label, `url` the destination
  as written (angle brackets kept), and `title` the double-quoted
  title or `None` (although annotated `str`).
- **LinkReference and ImageReference.** `reference` is the label in the
  last bracket pair, leading whitespace removed and trailing whitespace
  kept (`[ sp ]` gives `sp `). `text` is the text of the first bracket
  pair in the full form `[text][ref]`, and `None` in the shortcut form
  `[ref]`. The collapsed form `[c][]` is reported as the shortcut
  `[c]`.
- **Table.** `header`, `divider` and each entry of `rows` are lists of
  cell strings with the outer pipes removed and each cell stripped of
  whitespace. Divider cells keep their dashes and colons (`---`,
  `:-:`). `string` and `position` include the table's final newline.
- **List.** The fields exist but no `List` is ever produced.

### Utility Functions

```python
# tiredize/markdown/utils.py
def search_all_re(pattern: str, string: str) -> list[re.Match[str]]
def sanitize_text(pattern: str, text: str) -> str
```

`search_all_re` wraps `re.finditer` with `re.VERBOSE`. `sanitize_text`
replaces pattern matches with whitespace to preserve offsets. It splits
on `\n` (not `splitlines()`) to ensure trailing newlines in matched
regions are preserved in the output. The output length must always
equal the input length.

## File Layout

```
tiredize/markdown/
├── __init__.py
├── utils.py            search_all_re, sanitize_text
└── types/
    ├── __init__.py
    ├── code.py          CodeBlock, CodeInline
    ├── document.py      Document
    ├── frontmatter.py   FrontMatter
    ├── header.py        Header (+ slugify_header)
    ├── image.py         InlineImage
    ├── link.py          InlineLink, Autolink, ExtendedAutolink
    ├── list.py          List
    ├── quoteblock.py    QuoteBlock
    ├── reference.py     LinkReference, ImageReference,
    │                    ReferenceDefinition
    ├── schema.py        markdown schema validator (see its page)
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
immediately after a newline, and not after `|`, so a `|# Heading` in
a table cell is not a heading.

### URL Pattern in Inline Links and Images

`InlineLink` and `InlineImage` use `[^\s)]+` to capture URLs. The
`)` exclusion prevents the pattern from consuming past the closing
parenthesis into adjacent syntax. URLs containing literal `)` (e.g.,
balanced parentheses in Wikipedia URLs) are not supported.

### Pattern Reference

Each pattern is shown in `re.VERBOSE` form with named capture groups
and component descriptions. The autolink patterns are on
[autolinks](./autolinks.md).

#### `CodeBlock.RE_CODEBLOCK` (code.py)

```
(?:(?<=\n)|(?:^))       # Start-of-line anchor (zero-width)
(?P<delimiter>``[`]+)   # Opening fence: 3+ backticks
(?P<language>.*)        # Info string: rest of the opening line
\n                      # Newline after opening fence
(?P<code>[\s\S]*?)      # Code content (lazy, spans newlines)
\n                      # Newline before closing fence
\1                      # Closing fence: must match opening backtick count
```

The closing fence uses backreference `\1`, and nothing after it is
anchored: the closing line need only begin with the opening backtick
run. A longer closing run closes the block after the opening run's
length, and anything after the fence on the closing line is left
outside the block as ordinary text. A block with no content line
(an opening fence directly followed by its closing fence) is not
matched. `[\s\S]*?` is used instead of `.*?` because `.`
does not match newlines. The lazy quantifier prevents consuming
past the first matching closing fence.

#### `CodeInline.RE_CODE_INLINE` (code.py)

```
`                       # Opening backtick
(?P<code>[^\n`]+)       # Content: any chars except backtick or newline
`                       # Closing backtick
```

Does not support multi-backtick inline code (e.g., ` `` code `` `).
The `[^\n`]` exclusion prevents matching across lines.

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

Requires whitespace after the hashes, so a line like `#no-space`
will not match. `\s` includes tabs and line breaks: a line holding
only `#` (or `#` and spaces) becomes a heading whose title is the next
non-blank line, and that heading's `string` spans the lines between. The title captures everything to end-of-line
including trailing whitespace and closing `#` characters.

#### `Header.slugify_header` (header.py)

Generates GFM-compatible anchor slugs from heading text:

0. Replace an empty title with `section`.
1. Lowercase the text.
2. Remove characters that are not Unicode word characters (`\w`),
   spaces, or hyphens. This preserves non-ASCII letters (accented,
   CJK, Cyrillic, etc.), digits, and underscores while stripping
   punctuation. **Limitation:** `\w` excludes Unicode combining marks
   (category M), so NFD-decomposed diacritics (e.g., `Cafe\u0301`)
   are stripped rather than preserved.
3. Convert spaces to hyphens.
4. Collapse consecutive hyphens into one.
5. Strip leading and trailing hyphens.
6. Prepend `#`.
7. If the title matches a previously seen heading title, append
   `-1`, `-2`, etc. Deduplication is by exact title match, not by
   normalized slug.

No Unicode normalization is applied. Text in NFC form (where
accented characters are single codepoints) is preserved correctly.
Text in NFD form may lose combining marks due to the `\w`
limitation above.

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
but also means URLs without these characters are rejected. The end-of-line lookahead ensures definitions
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
references `[ref]`. It matches any bracketed text not followed by
`(` or `:`, whether or not a matching definition exists, so task-list
boxes (`- [ ]`, `- [x]`) and footnote markers (`[^1]`) are
`LinkReference` elements too. The `(?<!(!|\]))` lookbehind prevents matching
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
`depth` field (e.g., `>>` has depth 2), which counts only adjacent
`>` characters: `> > d` has depth 1 and quote `> d`. `\s` includes
line breaks, so a line holding only `>` takes the next non-blank line
as its quote, even when that line is an ordinary paragraph after a
blank line.

#### `Table.RE_TABLE` (table.py)

```
(?P<header>             # Header row:
    [|]?                #   Optional leading pipe
    ([^\n|]*[|])+       #   One or more cells followed by pipe
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
backtracking (see Design Decisions). A divider with no pipe at all
(a single-column `---`) therefore never matches. Data rows require
`|` on each line — a line without `|` terminates the table,
preventing the rows pattern from consuming non-table content. Cells
are split on every `|`, so an escaped `\|` or a pipe inside inline
code splits a cell.

## Sanitize Chain

Extractors call `sanitize()` on higher-precedence types before running
their own regex to avoid false matches. For example, link extraction
sanitizes out code blocks and inline code first because a URL inside a
fenced code block is not a rendered link.

The precedence order was set by comparing against GitHub's rendering,
not derived from the GFM specification, and no test checks the order
as a whole.

### Per-Extractor Sanitization Chains

Each extractor sanitizes internally before matching, independent of
calling context, ensuring correct results whether called from
`Section._extract()`, standalone scripts, or a future API.

| Extractor             | Sanitizes (in order)                      |
|-----------------------|-------------------------------------------|
| `CodeBlock`           | (none -- highest precedence)              |
| `CodeInline`          | CodeBlock                                 |
| `FrontMatter`         | (none -- extracted before Section parse)  |
| `Header`              | CodeBlock                                 |
| `InlineImage`         | CodeBlock, CodeInline                     |
| `InlineLink`          | CodeBlock, CodeInline                     |
| `Autolink`            | CodeBlock, CodeInline                     |
| `ExtendedAutolink`    | CodeBlock, CodeInline, InlineImage,       |
|                       | Autolink, InlineLink,                     |
|                       | ReferenceDefinition                       |
| `ReferenceDefinition` | CodeBlock                                 |
| `LinkReference`       | CodeBlock, CodeInline                     |
| `ImageReference`      | CodeBlock, CodeInline                     |
| `QuoteBlock`          | CodeBlock                                 |
| `List`                | (none)                                    |
| `Table`               | CodeBlock                                 |

**Design principle:** Code constructs have highest precedence
(content inside code is never interpreted as other elements).
ExtendedAutolink has the deepest chain because a bare URL is the most
ambiguous pattern: it blanks inline images, autolinks, inline links
and reference definitions, but not reference-style links or images; it is also the one extractor that
reads the original text alongside the blanked copy, because its
preceding-character rule must see the source character, not the blank
(see [autolinks](./autolinks.md)).

**Autolink blanking is span-based.** `Autolink.sanitize()` and
`ExtendedAutolink.sanitize()` blank exactly the spans their own
`extract()` reports, rather than re-running a pattern over the raw
text. A consequence: `Autolink.sanitize()` leaves a bracketed URI
inside inline code untouched, since `extract()` never reports it. Its
only in-package caller, `ExtendedAutolink.extract()`, has already
blanked code, so nothing observes the difference.

**QuoteBlock and link extractors:** Link extractors do not sanitize
QuoteBlock. Per GFM, blockquote content is real markdown — links
inside blockquotes are valid and should be extracted. The `>` prefix
does not interfere with any link regex pattern (none use
start-of-line anchors or characters that conflict with `>`).

### Section._extract() Orchestration

`Section._extract()` passes raw `string` to all extractors,
relying on each to sanitize internally.

The `string_safe` field stored on each `Section` is
`CodeInline.sanitize(CodeBlock.sanitize(string))`. It is not passed
to any extractor; it is stored for downstream consumers (e.g., linter
rules that need code-free text).

## Known Gaps

Elements other than the autolinks match only part of GFM. Unsupported
forms include indented code blocks, indented and tilde code fences,
unclosed fences, multi-backtick inline code, setext headings, URLs with
balanced parentheses, single quoted titles, a reference definition
title on its own line, lazy blockquote continuation, TOML or JSON
frontmatter, and CRLF line endings in text not read from a file (see
Entry Point). A reference definition's label and URL may sit on
different lines, and the pattern also accepts a blank line between
them, which GFM does not. Most known gaps have a skipped test in
`tests/markdown/types/` whose reason starts `gfm-parity:` (see
[testing](../practices/testing.md)); indented code blocks, unclosed
fences, balanced-parenthesis URLs, title-on-its-own-line definitions
and TOML or JSON frontmatter have none.

## Design Decisions

- **Each extractor sanitizes its own input,** whatever calls it, so it
  gives the same answer from `Section._extract()`, a script or a future
  API, at the cost of blanking the same text more than once.
- **The table divider has a mandatory `|` in each repeated group,**
  written as two alternatives. An optional pipe inside the repeat made
  long dash runs backtrack exponentially and hung on a real TRR.
- **A table header needs at least one `|`, and every data row needs
  one,** as GFM requires. This keeps blanked code lines from becoming
  headers and stops the rows pattern swallowing the prose that follows.
  A single-column header with only a trailing pipe (`Col |`) is
  therefore not recognised.
- **Link extractors do not blank block quotes,** because block quote
  content is markdown and GitHub renders links and images inside it.
  Reference definitions are not matched inside block quotes, because
  GFM scopes them to the quote.
- **`sanitize_text()` splits on `\n`, not `splitlines()`,** so blanked
  text keeps its length and its line endings, and start-of-line anchors
  after a blanked block still match.
- **Slugs keep Unicode letters** using `\w`, as GitHub does for NFC
  text, rather than ASCII ranges or the third-party `regex` module. Text
  is not normalized, so NFD combining marks are dropped.
- **Slugs are set on the existing `Header` objects after the section
  tree is built,** so the tree and `sections` share the same objects.
  `Header` and `Section` stay mutable for this.
