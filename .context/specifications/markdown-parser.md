# Specification: Markdown Parser

## Overview

The markdown parser converts raw markdown text into a tree of typed
dataclass elements. It owns the document model, element extraction,
text sanitization (to prevent false matches across element types), and
position tracking. Located in `tiredize/markdown/`.

The parser decides *what* a document contains; it never judges whether
an element is acceptable. Whether a link resolves, a line is too long,
or an element is disallowed belongs to the linter, which reads the
`Section` fields this subsystem populates. For the two autolink
elements the parser implements the GFM specification text (see
"Autolinks"), not GitHub's renderer: where the text and `cmark-gfm`
disagree, the text wins.

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

### Autolink Elements

```python
# tiredize/markdown/types/link.py
@dataclass(frozen=False)
class Autolink:                # GFM 0.29-gfm section 6.8
    position: Position
    string: str                # matched text, angle brackets included
    url: str                   # the URI as written, or mailto: + address

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[Autolink]
    @staticmethod
    def sanitize(text: str) -> str

@dataclass(frozen=False)
class ExtendedAutolink:        # GFM 0.29-gfm section 6.9
    position: Position
    string: str                # matched text as written, after trimming
    url: str                   # the href GitHub would navigate to

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> list[ExtendedAutolink]
    @staticmethod
    def sanitize(text: str) -> str
```

`string` is the GFM link label and `url` the GFM href. For
`ExtendedAutolink`, `url` is `string` unchanged for `http://`,
`https://`, `mailto:` and `xmpp:` links, `http://` + `string` for a
`www.` link, and `mailto:` + `string` for a bare email address. Neither
`extract()` raises on any input. `Section` exposes the results as
`autolinks: list[Autolink]` and `autolinks_extended:
list[ExtendedAutolink]`; the linter's element vocabulary names them
`autolink` and `autolink_extended`. The matching rules are in
"Autolinks" below.

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

#### `Header.slugify_header` (header.py)

Generates GFM-compatible anchor slugs from heading text:

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

#### `Autolink.RE_AUTOLINK` (link.py)

```
<                                   # Opening angle bracket
(?:
    (?P<uri>
        [A-Za-z][A-Za-z0-9+.\-]{1,31}   # Scheme, 2-32 characters
        :                               # Colon
        [^\x00-\x20\x7F<>]*             # No ASCII space/control/<>
    )
  | (?P<email>
        [a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+    # Local part
        @
        [a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?   # First label
        (?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*  # More
    )
)
>                                   # Closing angle bracket
```

The whole of GFM section 6.8 is this one pattern; there is no
post-processing. The `uri` branch is tried first, so `<mailto:x@y.z>`
is a URI whose `url` is written as-is, while `<x@y.z>` is an email
whose `url` gains `mailto:`. The email branch is the HTML5 regex the
specification reproduces: labels are 1-63 characters, may not start or
end with `-`, and the dotted part is optional, so `<x@y>` is an email
autolink. Backslashes inside the brackets are literal characters. See
"Autolinks" below.

#### `ExtendedAutolink.RE_CANDIDATE` (link.py)

```
(?:\A|(?<=[\s*_~(]))             # Start, whitespace, or * _ ~ (
(?:
    (?P<www>www\.[^\s<]*)         # www. then to whitespace or <
  | (?P<url>(?i:https?)://[^\s<]*)   # http(s):// likewise
  | (?P<protocol>mailto:|xmpp:)?  # Optional protocol, lower-case
    (?P<local>[A-Za-z0-9._+-]+)   # Local part, ASCII only
    @
    (?P<domain>                   # Domain segments, ASCII only
        [A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*
    )
    (?P<resource>                 # xmpp /resource, ASCII only
        /[A-Za-z0-9@]+(?:\.[A-Za-z0-9@]+)*
    )?
)
```

This is a *candidate* finder, not the extended autolink pattern: GFM
section 6.9 is procedural (count parentheses over the whole link,
inspect the last two domain segments, judge the character before the
link) and is not expressible in one regex. Each alternative captures
the longest run its form allows; the `_scan` pass in "Autolinks" below
then judges the preceding character, validates the domain and trims the
tail. The email alternative writes its domain and xmpp resource as
non-empty `.`-joined segments, so a trailing `.` falls outside the
match by construction rather than by trimming.

Two helper patterns serve the validation pass:

```
ExtendedAutolink.RE_DOMAIN       [\w-]+(?:\.[\w-]+)*
ExtendedAutolink.RE_ENTITY_TAIL  &[^\W_]+;\Z
```

`RE_DOMAIN` is matched against the text after `www.` or `http(s)://`
to find the domain a `www`/`url` candidate must begin with. Its `\w`
is deliberate: `www.`/`http` domains accept Unicode letters and digits,
whereas the email alternative above is ASCII-only (see "Decided
readings" under "Autolinks"). `RE_ENTITY_TAIL` recognises the
entity-like tail that path validation removes.

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
backtracking. See "Table divider regex rewrite" in Design
Decisions. Data rows require `|` on each line — a line without
`|` terminates the table, preventing the rows pattern from
consuming non-table content.

## Autolinks

`Autolink` and `ExtendedAutolink` implement GFM 0.29-gfm as published
at `https://github.github.com/gfm/` (dated 2019-04-06), sections 6.8
*Autolinks* and 6.9 *Autolinks (extension)*, examples 603-635, read
2026-09-18. The examples are pinned one-to-one, by number, in
`tests/markdown/types/test_link_gfm_autolinks.py`. The `test/spec.txt`
file in the `cmark-gfm` repository carries the same version string but
is older -- it numbers these examples 602-631, lists `ftp://` as an
extended scheme, and lacks `mailto:`/`xmpp:` -- and is not an authority
for this subsystem.

Where the specification text is silent, `cmark-gfm`
(`extensions/autolink.c`) breaks the tie; where both are unclear, the
user decides. The readings and divergences that follow are the result.
Neither extractor raises on any input.

### `Autolink` (section 6.8)

A match is `<`, then an absolute URI or an email address, then `>`,
with no whitespace inside. `RE_AUTOLINK` (Pattern Reference) is the
whole rule. An absolute URI is a 2-32 character scheme (ASCII letter,
then ASCII letters, digits, `+`, `.`, `-`), a colon, and zero or more
characters other than ASCII whitespace, ASCII control characters, `<`
and `>`; any scheme qualifies, so `<irc://…>`, `<a+b+c:d>` and
`<localhost:5001/foo>` are autolinks. An email address is anything the
HTML5 regex accepts. `string` includes the brackets; `url` is the URI
as written or `mailto:` + the address. Code blocks and inline code are
blanked before matching. Bare `http://example.com` and
`foo@bar.example.com` produce no `Autolink` (they are extended
autolinks).

### `ExtendedAutolink` (section 6.9)

A match is recognised only at the start of the text, after whitespace,
or after one of `*`, `_`, `~`, `(`, and is one of:

- `www.` + a valid domain + an optional path;
- `http://` or `https://` (any letter case) + a valid domain + an
  optional path -- `ftp://` is not an extended autolink;
- an email address: one or more of alphanumeric, `.`, `-`, `_`, `+`;
  `@`; one or more of alphanumeric, `-`, `_` separated by `.`, with at
  least one `.` and not ending in `-` or `_`;
- `mailto:` or `xmpp:` (lower-case) + an email address under the same
  rules; `xmpp:` additionally allows one `/` + a resource of
  alphanumerics, `@` and `.`; any further `/` ends the link. A `/`
  after a `mailto:` address is not part of the link.

A valid domain is segments of alphanumerics, `_` and `-` separated by
`.`, with at least one `.` and no `_` in the last two segments. The
path is zero or more non-whitespace, non-`<` characters, then trimmed
by extended autolink path validation: trailing `?`, `!`, `.`, `,`,
`:`, `*`, `_`, `~` are removed; when the link ends in `)` and holds
more `)` than `(`, the unmatched trailing `)` are removed; when it ends
in `;` preceded by `&` and one or more alphanumerics, that entity-like
tail is removed. The three rules repeat from the end until none
applies. A trailing `.` on an email address is never part of it.

`./`, `../` and `\`-prefixed tokens are never matched in any context.

#### Extraction passes

The rules above are applied in this order by `extract()`:

1. **Blank.** Code blocks, inline code, images, autolinks, inline
   links and reference definitions are blanked to spaces (same length),
   so a URL inside `` ` ` ``, `[text](url)` or `<url>` is never also an
   extended autolink.
2. **Candidate.** `_scan` searches the blanked copy with
   `RE_CANDIDATE`, which anchors on the preceding-character rule and
   captures the longest run each form allows.
3. **Start** (`_start`). For a bare email candidate the link begins at
   the maximal backward run of local-part characters
   (`LOCAL_PART_CHARACTERS`, `[A-Za-z0-9._+-]`) before the `@`; for
   every other form it begins at the candidate. This matters because
   `_` is both a local-part character and a preceding delimiter.
4. **Preceding character** (`_valid_preceding`). Judged on the
   *original* text at that start, not on the blanked copy: a link
   glued to the end of a blanked construct (`[x](u)www.c.d`,
   `` `code`https://c.d ``) follows `)` or a backtick in the source and
   is rejected. Whitespace is `str.isspace()`, the set `\s` matches;
   the other admitted characters are `PRECEDING_DELIMITERS` (`*_~(`).
5. **Validate** (`_validate_url` / `_validate_email`). A `www`/`url`
   candidate must begin with a domain (`RE_DOMAIN`) that has at least
   one `.` and no `_` in its last two segments; the run is then
   trimmed by `_trim` (the three path-validation rules, using
   `TRAILING_PUNCTUATION` and `RE_ENTITY_TAIL`). An email or protocol
   candidate is rejected outright when its domain ends in `-` or `_`;
   a `/resource` is kept only for `xmpp:`.
6. **Resume.** A rejected candidate is skipped by one character, so a
   valid link that starts inside it after a delimiter
   (`http://nodot(www.a.b)` yields `www.a.b`) is still found. After an
   accepted link, scanning resumes at its trimmed end, so links never
   overlap.

`string` is `text[start:end]` as written; `url` derives from it as the
Autolink Elements contract states. `sanitize()` blanks exactly the
spans `extract()` reports. Because the matcher is context-sensitive,
`ExtendedAutolink.sanitize()` is not idempotent in general: blanking an
accepted link turns the character before whatever was glued to it into
whitespace, so a second pass can accept a candidate the first rejected
(`a@b.c+d@f.g` blanks `a@b.c` on the first pass and `+d@f.g` on the
second). No in-package caller applies it to its own output.

Both extractors are linear on prose. A single multi-kilobyte
whitespace-free token built from `_`, `&…;` runs, or a long `_`-laden
local part behind an invalid preceding character is quadratic (seconds
at 10-40 kB), never exponential.

### Decided readings where the specification is silent

Each of these follows `cmark-gfm` and is pinned in
`tests/markdown/types/test_link.py`.

- **"Alphanumeric"** is Unicode in `www.`/`http(s)` domains
  (`RE_DOMAIN` uses `\w`, so `www.bücher.example` and
  `https://münchen.de/x` link) and ASCII in email addresses -- local
  part, domain and xmpp resource, for the bare, `mailto:` and `xmpp:`
  forms alike -- so `josé@b.c` and `jose@exämple.com` produce nothing.
- **A non-ASCII character in an email domain or xmpp resource ends the
  link rather than voiding it**: `jose@example.cöm` links as
  `jose@example.c`, `xmpp:a@b.c/ré` as `xmpp:a@b.c/r`. Before the `@`
  a non-ASCII character voids the address, since it is neither a
  local-part character nor a valid preceding character.
- **A bare email address begins at the maximal backward run of
  local-part characters before the `@`**, and the preceding-character
  rule is judged there. `"first_last@example.com"` yields nothing
  (the whole address follows `"`; no `last@example.com` fragment is
  produced), while `www.a_b@c.d` links as `mailto:www.a_b@c.d`.
- **`www.` + a single segment links**: `www.a` and `www.localhost`
  are links, because the `www` segment satisfies "at least one
  period".
- **Scheme letter case.** `http://`/`https://` match
  case-insensitively (`HTTP://a.b` links; `string` and `url` keep the
  case as written); `mailto:` and `xmpp:` are case-sensitive, so
  `MAILTO:a@b.c` is neither a protocol autolink nor a bare email (`:`
  is an invalid preceding character).

### Known divergences from cmark-gfm

Here the published text and GitHub's renderer disagree and the text is
followed. Each is pinned in `tests/markdown/types/test_link.py`. None
produces a wrong `links` finding, since `mailto:`/`xmpp:` targets are
not checked and the `http`/`www.` cases differ only in a trailing
character or in whether a link is recognised at all.

1. **Trailing `;`, `'`, `"` stay part of an extended autolink.** The
   specification's trailing-punctuation list omits them; `cmark-gfm`
   strips all three. `see www.a.b/x;` links `www.a.b/x;` here and
   `www.a.b/x` on GitHub. An entity-like `&name;` tail is still removed
   (that rule is in the text).
2. **The preceding-character rule applies to all four extended forms
   and is judged on the source text.** `cmark-gfm` applies it to
   `www.` only, so `"https://x.org"` and `"foo@bar.com"` link on
   GitHub but not here; `(https://x.org)` and `see foo@bar.com` link
   in both.
3. **The `&name;` entity tail uses Unicode alphanumerics** (`[^\W_]`)
   where `cmark-gfm` accepts ASCII letters only, so `www.a.b/x&hl2;`
   links as `www.a.b/x` here and `www.a.b/x&hl2` on GitHub.
4. **Whitespace is Unicode** (`str.isspace()` / `\s`) in both the
   preceding-character rule and path termination, whereas the
   specification's section 2.1 and `cmark-gfm` use the ASCII set. A
   link preceded by U+00A0 or U+3000 is admitted here and not on
   GitHub; such a character inside a path ends the link here but not
   there.
5. **A double-`@` token links its leftmost valid address.**
   `a@b.c@d.e` links `a@b.c` here; `cmark-gfm` rejects a domain run
   holding a second `@` and links from the second `@`'s local part
   instead.
6. **`http://localhost/x` is not an extended autolink** because the
   text requires at least one `.` in the domain; `cmark-gfm`'s url
   matcher allows a dot-less domain. (`<http://localhost/x>` is an
   `Autolink` in both.)
7. **An email whose domain ends in a digit links** (`a@b.c1`,
   `a@b.1`): the text forbids only a final `-` or `_`, whereas
   `cmark-gfm` requires a letter or `.`.
8. **`xmpp:a@b.c/` links as `xmpp:a@b.c`**; `cmark-gfm` produces no
   link for a trailing empty resource.

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

**Design principle:** The chain order follows GFM rendering
precedence. Code constructs have highest precedence (content inside
code is never interpreted as other elements). ExtendedAutolink has the
deepest chain because a bare URL is the most ambiguous pattern and
must exclude every other link type; it is also the one extractor that
reads the original text alongside the blanked copy, because its
preceding-character rule must see the source character, not the blank
(see "Autolinks").

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
start-of-line anchors or characters that conflict with `>`). See
issue `quoteblock-over-sanitization.md`.

### Section._extract() Orchestration

`Section._extract()` passes raw `string` to all extractors,
relying on each to sanitize internally.

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

- **Table header requires at least one pipe:** The header group in
  `RE_TABLE` uses `([^\n|]*[|])+` (one or more) rather than
  `([^\n|]*[|])*` (zero or more). This ensures the header only matches
  lines containing at least one pipe character, preventing
  whitespace-only lines (produced by `CodeBlock.sanitize()`) from
  matching as table headers. See issue
  `table-header-empty-indexerror.md`.

- **Table extraction sanitizes internally:** `Table.extract()` calls
  `CodeBlock.sanitize()` on its input before matching, consistent with
  all other extractors. This prevents false table matches inside code
  fences. Previously, sanitization was handled externally by
  `Section._extract()` — see issue `table-internal-sanitization.md`.

- **Autolinks are GFM parity, not a superset.** `ExtendedAutolink`
  matches exactly what GFM section 6.9 links and nothing else. `./`,
  `../` and `\` paths in prose are plain text on GitHub and are not
  matched; relative documentation links are still validated, because
  GitHub resolves them only inside `[text](./path)` and `[ref]: ./path`
  and both already reach the linter. A superset cannot be predicted
  from GitHub's rendering and every extra match could only ever be a
  false positive. See issue `autolink-gfm-parity.md`.

- **The specification text is followed concretely; `cmark-gfm` breaks
  ties.** The published text is a concrete, versioned, testable
  definition; the reference implementation drifts from it and tracking
  it would mean re-auditing C source on every release. Where the two
  disagree the text wins and the difference is recorded under "Known
  divergences from cmark-gfm"; where the text is silent, `cmark-gfm`'s
  behaviour is adopted and recorded under "Decided readings"; where
  both are unclear, the user decides. Reversing this would move every
  divergence listed above.

- **`url` is the GFM href and `string` the GFM label.** GFM renders
  `www.commonmark.org` with `href="http://www.commonmark.org"` and
  `foo@bar.baz` with `href="mailto:foo@bar.baz"`. The normalised
  target goes in `url`, so the `links` rule and any consumer sees the
  address GitHub would navigate to, while `string` and `position`
  describe the source text. No extra field carries the normalisation.

- **The autolink elements take the specification's names, with no
  alias.** The classes are `Autolink` and `ExtendedAutolink`, the
  `Section` fields `autolinks` and `autolinks_extended`, and the
  linter vocabulary `autolink` and `autolink_extended` (keeping the
  `<element>_<qualifier>` shape of `image_inline`). The former names
  `BracketLink`/`BareLink`, `links_bracket`/`links_bare` and
  `link_bracket`/`link_bare` are not accepted anywhere: a rules file
  naming them fails at load with the unknown-element error. Carrying
  deprecated names would leave the specification's terms competing
  with tiredize's in the documentation.
