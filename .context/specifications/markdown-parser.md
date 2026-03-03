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

Each extractor sanitizes internally before matching, independent of
calling context. This ensures correct results whether called from
`Section._extract()`, standalone scripts, or a future API.

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
