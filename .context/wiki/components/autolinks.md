# Autolinks

## Overview

`Autolink` and `ExtendedAutolink` are the two parser elements that
follow the GFM specification exactly, so a user can predict from
GitHub's rendering what tiredize treats as a link. This page holds their
contract, patterns and matching rules. The rest of the parser, including
the sanitize chain these extractors take part in, is on [markdown
parser](./markdown-parser.md). How the `links` rule checks the targets
is on [linter rules](./linter-rules.md).

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

## Contracts and Interfaces

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
`autolink` and `autolink_extended`. The matching rules follow.

## Patterns

### `Autolink.RE_AUTOLINK` (link.py)

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
autolink. Backslashes inside the brackets are literal characters. See Autolink below.

### `ExtendedAutolink.RE_CANDIDATE` (link.py)

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
whereas the email alternative above is ASCII-only (see Decided Readings). `RE_ENTITY_TAIL` recognises the
entity-like tail that path validation removes.

## `Autolink` (section 6.8)

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

## `ExtendedAutolink` (section 6.9)

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

### Extraction Passes

The rules above are applied in this order by `extract()`:

1. **Blank.** Code blocks, inline code, images, autolinks, inline
   links and reference definitions are blanked to spaces (same length),
   so a URL inside inline code, an inline link or an autolink is never
   also an extended autolink.
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

## Decided Readings

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

## Known Divergences from cmark-gfm

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

## Design Decisions

- **GFM parity, not a superset.** `ExtendedAutolink` matches exactly
  what GFM section 6.9 links. `./`, `../` and `\` paths in prose are
  plain text on GitHub and are not matched; relative documentation links
  are still checked, because GitHub resolves them only inside
  `[text](./path)` and `[ref]: ./path`, which reach the linter anyway. A
  superset cannot be predicted from GitHub's rendering, and every extra
  match could only be a false positive.
- **The published specification text is followed; `cmark-gfm` breaks
  ties.** The text is concrete, versioned and testable; the reference
  implementation drifts from it, and tracking it would mean re-auditing
  C source on every release. Where the two disagree the text wins and
  the difference is listed under Known Divergences; where the text is
  silent `cmark-gfm` is followed and listed under Decided Readings;
  where both are unclear the user decides.
- **The published page is the authority, not `cmark-gfm`'s
  `test/spec.txt`,** which carries the same version string but is older.
- **`url` is the GFM href and `string` the GFM label.** GFM renders
  `www.commonmark.org` with `href="http://www.commonmark.org"` and
  `foo@bar.baz` with `href="mailto:foo@bar.baz"`, so the `links` rule
  sees the address GitHub would navigate to, while `string` and
  `position` describe the source text. No extra field carries the
  normalisation.
- **The elements take the specification's names, with no alias:**
  classes `Autolink` and `ExtendedAutolink`, `Section` fields
  `autolinks` and `autolinks_extended`, and linter names `autolink` and
  `autolink_extended`, keeping the `<element>_<qualifier>` shape of
  `image_inline`. Old names would compete with the specification's terms
  in the documentation.
- **Code is blanked before autolinks are matched,** whereas GFM gives
  code spans and autolinks equal precedence from left to right. The two
  differ only when a backtick opens before an autolink that contains one.
