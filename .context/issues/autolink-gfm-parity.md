---
assignee: software-engineer
created: 2026-09-14
knowledge: []
priority: medium
status: in-progress
step: implementation
tags: [gfm-parity, parser, pr-44]
type: bug
workflow: software-engineering
---

# Autolinks Match the GFM Specification

## Summary

Tiredize recognises autolinks — URLs that become links without
`[text](url)` syntax — by its own rules, which are neither a subset nor
a superset of GitHub-Flavored Markdown's. Anyone using the tool on a
repository GitHub renders will expect the two to agree: what GitHub
shows as a link, tiredize validates; what GitHub shows as plain text,
tiredize leaves alone. Today they disagree in both directions, and the
disagreement is what a real user hit: prose that GitHub renders as
plain text was reported as an unreachable link.

This issue makes tiredize's autolink handling, traditional and
extended, match the GFM specification exactly — the *Autolinks*
section (§6.8) and the *Autolinks (extension)* section (§6.9) of GFM
0.29-gfm as published at `https://github.github.com/gfm/`. It renames
the two elements to the specification's own terms, and adjusts the
`links` rule so that recognising the additional link forms does not
produce findings for links that cannot be checked.

Inline links, reference links, and images are a different category of
syntax with their own specification sections. They are not visibly
broken for users and stay in the `gfm-parity` register for later.

### Origin

The issue began as a narrow bug: `BareLink.RE_URL` treats a backslash
as the start of a Windows path, GFM treats it as an escape character,
and the two are indistinguishable in prose. Escaped punctuation such as
`\*.dll`, `\|`, `\_hidden\_`, and `\\attacker\share` was extracted as a
bare link and reported unreachable. The backslash branch cannot produce
a true positive — `check_url_valid()` only resolves `.`-prefixed paths
locally, so every backslash match falls through to HTTP validation and
fails — so every match was noise. That fix was verified in a throwaway
worktree: deleting `|\\` from the pattern clears every case and fails
exactly one test, the one asserting the removed behaviour.

Scoping on 2026-09-18 established that the fix was a half-measure. The
stated goal, put to the PR #44 contributor directly, is that link
identification matches GitHub's; removing one collision while leaving
`./` paths (which GitHub never links), `www.` autolinks (which GitHub
always links), and trailing-punctuation handling untouched would leave
the parser in a state no user can predict from GitHub's behaviour. The
scope was expanded to the whole of the two spec sections.

### Current behaviour against the specification

| Specification rule (GFM 0.29) | Tiredize today |
| --- | --- |
| `<scheme:…>` is a link for **any** 2–32 character scheme: `<irc://…>`, `<MAILTO:…>`, `<a+b+c:d>`, `<localhost:5001/foo>` | `<https?://…>` only |
| `<email>` per the HTML5 email regex is a link to `mailto:` + address | not matched |
| Bare `http://` or `https://` + valid domain is a link | `http(s)://` matched, no domain check |
| Bare `www.` + valid domain is a link; `http://` is inserted | not matched |
| Bare email address is a link to `mailto:` + address | not matched |
| Bare `mailto:` or `xmpp:` + email address is a link; `xmpp:` allows one `/resource` | not matched |
| Bare autolinks recognised only at line start, after whitespace, or after `*`, `_`, `~`, `(` | `http(s)://` matched anywhere, including mid-word |
| Trailing `?`, `!`, `.`, `,`, `:`, `*`, `_`, `~` excluded from the link | captured as part of the URL |
| Unbalanced trailing `)` excluded; entity-like `&xxx;` tail excluded; `<` ends the link | captured as part of the URL |
| Valid domain: alphanumeric, `_`, `-` segments separated by `.`; at least one `.`; no `_` in the last two segments | no domain validation |
| Backslash escapes do not work inside `<…>` autolinks | n/a — pattern never reaches them |
| `./`, `../`, `\` paths are plain text | matched as bare links |

The authoritative text is the published specification at
`https://github.github.com/gfm/`, sections 6.8 and 6.9. Its numbered
examples 603–621 (autolinks, 19) and 622–635 (extension, 14) are the
33 conformance cases this issue is measured against. The `test/spec.txt`
file on the `github/cmark-gfm` default branch carries the same version
string but is older: it numbers these examples 602–631, still lists
`ftp://` as an extended URL scheme, and lacks the extended protocol
autolinks. It must not be used for example numbers or rules.

### Public Contract

Two parser elements are renamed and rewritten, and one linter rule
changes.

**Names.** The specification's terms replace tiredize's:

| Today | After | Where it appears |
| --- | --- | --- |
| `BracketLink` | `Autolink` | class in `tiredize/markdown/types/link.py` |
| `BareLink` | `ExtendedAutolink` | class in `tiredize/markdown/types/link.py` |
| `Section.links_bracket` | `Section.autolinks` | dataclass attribute |
| `Section.links_bare` | `Section.autolinks_extended` | dataclass attribute |
| `link_bracket` | `autolink` | element vocabulary: `elements.disallow`, `line_length.exclude`, `unicode.exclude` |
| `link_bare` | `autolink_extended` | element vocabulary, as above |
| "Bracket link" | "Autolink" | `elements` label; `links` rule finding message |
| "Bare link" | "Extended autolink" | `elements` label; `links` rule finding message |

A rules file that still names `link_bare` or `link_bracket` fails at
configuration load with the existing
`Unknown element name in disallow: '…'` error. No alias is provided.

**`Autolink.extract(text: str, base_offset: int = 0) ->
list[Autolink]`** — implements GFM §6.8. A match is `<`, an absolute
URI or an email address, `>`, with no whitespace inside. Each result
carries:

- `string` — the full matched text including the angle brackets;
- `url` — the link target: the URI as written for a URI autolink, or
  `mailto:` followed by the address for an email autolink;
- `position` — offset and length of `string` within `text`.

An absolute URI is a scheme (2–32 characters, ASCII letter first, then
ASCII letters, digits, `+`, `.`, `-`), a colon, and zero or more
characters other than ASCII whitespace, control characters, `<`, and
`>`. An email address is anything matching the HTML5 email regex
reproduced in the specification. Backslashes inside the brackets are
literal characters, not escapes. The negative cases in examples
615–621 (`<foo\+@bar.example.com>`, `<>`, `< http://foo.bar >`,
`<m:abc>`, `<foo.bar.baz>`, and bare `http://example.com` /
`foo@bar.example.com` with no brackets) produce no `Autolink`. Note
that the last two are still extended autolinks under §6.9.

**`ExtendedAutolink.extract(text: str, base_offset: int = 0) ->
list[ExtendedAutolink]`** — implements GFM §6.9. A match is recognised only at
the start of `text`, after whitespace, or after one of `*`, `_`, `~`,
`(`, and is one of:

- `www.` followed by a valid domain and an optional path;
- `http://` or `https://` followed by a valid domain and an optional
  path (`ftp://` is not an extended autolink; it is only a link inside
  `<…>`);
- an email address per the extension's rules: one or more of
  alphanumeric, `.`, `-`, `_`, `+`; then `@`; then one or more of
  alphanumeric, `-`, `_` separated by `.`, with at least one `.`, not
  ending in `-` or `_`;
- `mailto:` or `xmpp:` followed by an email address under the same
  rules; `xmpp:` additionally allows one `/` followed by a resource of
  alphanumerics, `@`, and `.`, with any further `/` ending the link.
  A `/` after a `mailto:` address is not part of the link.

The path is zero or more non-space, non-`<` characters, then trimmed by
extended autolink path validation: trailing `?`, `!`, `.`, `,`, `:`,
`*`, `_`, `~` are excluded; when the match ends in `)` and contains more
`)` than `(`, the unmatched trailing `)` are excluded; when it ends in
`;` preceded by `&` and one or more alphanumerics, that entity-like
tail is excluded. A trailing `.` on an email address is excluded. Each
result carries:

- `string` — the matched text exactly as it appears in `text`, after
  trimming;
- `url` — the link target: `string` unchanged for `http`, `https`,
  `mailto:`, and `xmpp:`; `http://` + `string` for `www.`; `mailto:` +
  `string` for a bare email address;
- `position` — offset and length of `string` within `text`.

`./`, `../`, and `\`-prefixed tokens are never matched, regardless of
context.

**`Autolink.sanitize(text)` and `ExtendedAutolink.sanitize(text)`**
blank exactly the spans their `extract()` would match.

**Sanitization order** is unchanged: both extractors run on text with
code blocks and inline code already blanked, and `ExtendedAutolink`
additionally runs after images, autolinks, inline links, and reference
definitions are blanked, so a URL inside `[text](url)` or `<url>` is
never also an extended autolink.

**`links` rule** — validates `url` values whose scheme is `http` or
`https`, which after normalisation includes every `www.` extended
autolink. Anchors (`#slug`) and `.`-prefixed relative paths continue
to be resolved as today; those arrive from inline links and reference
definitions, never from autolinks. A link with any other scheme
(`mailto:`, `xmpp:`, `irc:`, `ftp:`, or an unregistered one such as
`a+b+c:`) is recognised by the parser but produces no finding from the
rule. Finding messages name the element as "Autolink" or "Extended
autolink". The `exclude` option continues to match on hostname.

**Error behaviour.** None. Neither extractor raises on any input, and
`check_url_valid()` continues to return failures as tuples.

## Acceptance Criteria

Acceptance tests (written at step 2, before implementation):

- [ ] Every one of the 33 specification examples 603–635 has an
      acceptance test that feeds the example's markdown to
      `Autolink.extract()` or `ExtendedAutolink.extract()` as
      appropriate and asserts the exact set of links extracted —
      `string` and `url` for each, and an empty list for the negative
      cases. Each test names the example number as published at
      `https://github.github.com/gfm/`. Examples containing several
      input paragraphs assert every paragraph; none is partially
      covered. Examples 617, 620, and 621 assert both that no
      `Autolink` is extracted and that one `ExtendedAutolink` is — for
      617, `http://foo.bar` follows whitespace and so qualifies under
      §6.9 even though `< http://foo.bar >` fails §6.8.
- [ ] The preceding-character rule is tested beyond the spec examples:
      an extended autolink after each of `*`, `_`, `~`, `(` is matched;
      the same URL immediately after a letter, digit, or `"` is not.
- [ ] The escape cases that opened this issue are tested as producing
      no extended autolink: `\*.dll`, `\|`, `\_x\_.md`,
      `\\server\share`, and an escaped sequence ending in a file
      extension. `./configure` and `../guide.md` in running prose are
      tested as producing no extended autolink.
- [ ] Relative path validation through inline links
      (`[text](./file.md)`) and reference definitions
      (`[ref]: ./file.md`) is tested as unchanged.
- [ ] The `links` rule is tested to produce no finding for autolinks
      and extended autolinks whose scheme is not `http` or `https`, to
      validate a `www.` extended autolink against `http://` + the
      matched text, and to name the element as "Autolink" or "Extended
      autolink" in finding messages.
- [ ] `Autolink.sanitize()` and `ExtendedAutolink.sanitize()` are
      tested to blank exactly the spans `extract()` matches, including
      a trailing-punctuation case where the blanked span must stop
      before the punctuation.
- [ ] The `elements` rule is tested to accept `autolink` and
      `autolink_extended` in `disallow`, to label findings "Autolink"
      and "Extended autolink", and to reject `link_bare` and
      `link_bracket` as unknown names. The `line_length` and `unicode`
      rules, which share the element vocabulary in their `exclude`
      lists, are tested the same way. (Corrected at the step-2 gate:
      the criterion originally placed `exclude` on `elements`, which
      has no such option.)
- [ ] All of the above fail before implementation and pass after.

Implementation:

- [ ] `BracketLink` is renamed `Autolink` and `BareLink` is renamed
      `ExtendedAutolink`, with `Section.autolinks` and
      `Section.autolinks_extended` replacing `links_bracket` and
      `links_bare`, and the `elements` vocabulary and labels updated per
      the Public Contract. No reference to the old names remains in
      `tiredize/`, and none in `tests/` outside the tests that assert
      the old names are rejected. (Corrected after step 3: the
      original wording contradicted the rejection tests.)
- [ ] `Autolink` matches per GFM §6.8 as stated in the Public Contract.
- [ ] `ExtendedAutolink` matches per GFM §6.9 as stated in the Public
      Contract, including extended autolink path validation.
- [ ] The `./`, `../`, and `\` alternatives are gone from the extended
      autolink pattern.
- [ ] The `links` rule validates only `http` and `https` targets and
      emits no finding for other schemes.
- [ ] The four skipped tests `test_bare_link_www`,
      `test_bare_link_trailing_punctuation_stripped`,
      `test_bracket_link_ftp`, and `test_bracket_link_email` are
      unskipped and pass, or are superseded by the example-numbered
      tests and removed.
- [ ] `test_bare_link_backslash` is inverted to assert no match and
      renamed to reflect that backslash paths are not autolinks;
      `test_bare_link_backslash_not_matched_mid_word` is retained,
      renamed to the new vocabulary, and given a docstring stating that
      it asserts registry keys are not links.
- [ ] The full test suite passes and flake8 reports nothing.

Documentation:

- [ ] `.context/specifications/markdown-parser.md` — the element
      descriptions, the Relative Path Matching section, the Pattern
      Reference entries, and every mention of the two elements use the
      new names and reflect the new behaviour. The sentence "Backslash
      paths (`\`) are also supported for Windows-style paths" is gone.
      The Pattern Reference block for the extended autolink pattern is
      already stale (it shows a superseded form with `\S+`).
- [ ] `README.md` — the `links` rule section states which link forms
      are recognised and that only `http` and `https` targets are
      checked; the Recognized markdown element names table lists
      `autolink` and `autolink_extended` in place of `link_bare` and
      `link_bracket`; the parser feature description no longer says
      "bracket" or "bare".
- [ ] `.context/issues/gfm-parity.md` — the BareLink and BracketLink
      register entries are checked off and their Findings entries
      updated, since this issue delivers those two elements.

## Design Decisions

### Parity is the principle; the superset is gone

`BareLink` was a deliberate superset of GFM: it matched `./`, `../`,
and `\` paths that GitHub renders as plain text, on the reasoning that
validating relative documentation links is the rule's purpose. That
reasoning is sound but the mechanism was wrong. GitHub resolves relative
links only inside `[text](./path)` and `[ref]: ./path`, and tiredize
already validates both through `check_url_valid()`. Removing relative
path matching from bare links loses no validation that GitHub's own
rendering would justify, and removes a false-positive class of the same
shape as the backslash bug: prose such as "run ./configure" outside
inline code was extracted and checked for a file that does not exist.

Validating Windows paths remains out of scope. If it is ever wanted it
is a feature needing a design, not a regex branch that can only emit
errors.

### The specification examples are the oracle

"1:1 with GFM" is not a judgment call if the tests are the
specification's own examples. Step 2 transcribes examples 603–635 into
tests that assert extraction results, not rendered HTML — tiredize is
a parser, not a renderer, so `&amp;` in the spec's HTML output is
irrelevant and the URL is compared as written in the source. Each test
carries the example number so a reader can check it against the
specification without trusting the test author. The examples are short
enough that the tests themselves become the in-repo record and no copy
of the specification is committed.

The published site is the authority, not the `cmark-gfm` repository's
`test/spec.txt`. The two were compared during scoping and differ under
the same version string: the file is behind by one section (§6.5
versus §6.8), by one to four example numbers, and by two rules —
`ftp://` as a bare autolink scheme (dropped on the site) and the
extended protocol autolinks `mailto:`/`xmpp:` (added on the site). A
verbatim copy of the site's two sections, taken 2026-09-18, is handed
to the qa-engineer at step 2.

### Boundary: this issue is the register's BareLink and BracketLink entry

GFM's *Autolinks* and *Autolinks (extension)* sections together define
every way a URL in prose becomes a link without `[…](…)` syntax, and
they map exactly onto what tiredize called `BracketLink` and
`BareLink`. `InlineLink` is governed by a different section (*Links*),
has different rules (balanced parentheses, angle-bracket destinations,
titles), and shares design themes with `InlineImage` and
`ReferenceDefinition` per the `gfm-parity` cross-cutting table. It is
not what broke for users, and it stays in the register as its own
element. This issue carries the `gfm-parity` tag and closes the
BareLink and BracketLink lines there. Confirmed by the user at the
scoping gate, 2026-09-18.

Autolinks and code spans have equal precedence in GFM and are resolved
left to right by start position. Tiredize blanks code first, which
differs only in the pathological case of a backtick opening before an
autolink that itself contains a backtick. That is a `CodeInline`
concern and stays with the register.

### `url` is the GFM href, `string` is the GFM label

GFM renders `www.commonmark.org` with `href="http://www.commonmark.org"`
and `foo@bar.baz` with `href="mailto:foo@bar.baz"`. Tiredize already
distinguishes `string` (matched text) from `url` (target). The
normalised target goes in `url`, so the `links` rule and any consumer
sees the address GitHub would navigate to, while `string` and
`position` describe the source text. No new field is needed.

### The `links` rule checks only what it can check

Parity makes the parser recognise `<irc://…>`, `<a+b+c:d>`,
`<localhost:5001/foo>`, `<foo@bar.example.com>`, bare email addresses,
and bare `mailto:`/`xmpp:` links. None can be validated with an HTTP
request; handing them to `requests.get()` reports every one as
unreachable. That would replace the false positives this issue removes
with a larger set. The rule therefore validates `http` and `https`
targets only. Other schemes are recognised — they count as links for
the `elements` rule and are available to any future rule — but produce
no finding. Confirmed by the user at the scoping gate, 2026-09-18.

### The elements take the specification's names

Tiredize's element vocabulary predates its author's reading of the GFM
specification. "Bracket link" and "bare link" appear nowhere in the
specification; the terms are *autolink* (§6.8) and *extended autolink*
(§6.9). Since this issue rewrites both elements, their tests, their
specification sections, and their README text, doing so under names
the specification does not use and renaming later would mean writing
the documentation twice. The classes become `Autolink` and
`ExtendedAutolink`; the `elements` vocabulary becomes `autolink` and
`autolink_extended`, keeping the existing `<element>_<qualifier>`
shape of `image_inline` and `link_reference`.

This is a breaking change to the `elements` rule configuration. A
rules file naming `link_bare` or `link_bracket` fails at load with the
existing unknown-element error, which names the offending key. No
alias is kept: the vocabulary is small, the error is explicit, and
carrying deprecated names forward would leave the specification's
terms competing with tiredize's in the documentation.

The remaining non-GFM names — `CodeInline`/`code_inline` (spec: *code
span*), `QuoteBlock`/`quoteblock` (*block quote*), `Header`/`header`
(*heading*), `ReferenceDefinition`/`reference_definition` (*link
reference definition*) — are a pure rename with no behaviour change and
are out of scope here. They should be filed as one dedicated issue so
users see a single further breaking change rather than one per
element.

### The specification is followed concretely; cmark-gfm breaks ties

Decided by the user after step 3, 2026-09-18. Where the published
specification text and GitHub's reference implementation (`cmark-gfm`,
`extensions/autolink.c`) disagree, the specification wins. It is a
concrete, versioned, testable definition; the implementation drifts
from it (it has dropped `ftp://` as an extended scheme and added
`mailto:`/`xmpp:` since the text was written) and tracking it would
mean re-auditing C source on every release. The known divergences are
all in the tails and none produces a wrong finding:

- Trailing `;`, `'`, `"` stay part of an extended autolink. The
  specification's trailing-punctuation list does not include them;
  `cmark-gfm` strips all three (`;` as an entity if preceded by
  `&name`, otherwise alone).
- The preceding-character rule (line start, whitespace, `*`, `_`,
  `~`, `(`) applies to all four extended forms, as the §6.9 text
  states. `cmark-gfm` applies it only to `www.`, so `"https://x.org"`
  and `"foo@bar.com"` link on GitHub but not here.

Where the specification is **silent**, do what `cmark-gfm` does; if
that is also unclear, the user decides. The first application is the
meaning of "alphanumeric" in valid domains and email addresses, which
the specification never defines: `cmark-gfm` accepts Unicode
letters and digits in `www.`/`http` domains but ASCII only in email
local parts and domains, so tiredize does the same. (Step 3 had read
Unicode for both; this is a one-line correction routed back to
step 3.)

The parser specification at step 6 must pin the specification
version and read date (0.29-gfm, published 2019-04-06, read
2026-09-18 from `https://github.github.com/gfm/`) and carry this
divergence list, so a user who meets one finds it documented.

### The `links` scheme gate is uniform across link kinds

Decided by the user after step 3. The http/https-only gate applies to
inline links and reference definitions as well as autolinks, so a
`[text](mailto:…)` or `[ref]: ftp://…` no longer produces a guaranteed
false positive. Step 3 implemented it this way; the contract had only
spoken of autolinks, and the user confirmed the extension rather than
have it deferred.

### Out-of-scope defects become skipped regression tests

Decided by the user after step 3. A defect found during this issue
but outside its criteria is recorded as a failing unit test, verified
to fail, then skipped with `reason="<issue-slug>: …"` naming a filed
issue. The first use is the `_is_excluded()` crash on a malformed URL
when `exclude` is configured, tracked as
`links-exclude-malformed-url-crash` (draft). The convention itself is
proposed for the dotclaude standard, not defined here.

### Scoping seeds

These seed the technical-architect's later judgment. They are seeds,
not commitments — the architect makes the final calls at steps 6 and 7.

**Step 6 — does this change a subsystem's behavior or public contract?
Seed: yes.** Two parser elements are renamed, change what they match
and what `url` carries, and a linter rule changes which links it
validates. The parser
specification documents the current patterns and a Relative Path
Matching section that becomes false; the linter specification describes
the `links` rule. The acceptance criteria name the parser specification
passages; the architect should also check `linter.md` for the `links`
rule and `check_url_valid` description, which is already known to be
stale (it omits `valid_status_codes`).

**Step 7 — does this need user-facing documentation? Seed: yes.** The
README's `links` rule section says the rule checks "inline links,
angle-bracket links, bare URLs, and reference definitions" and says
nothing about which schemes are checked. After this change a user
reading a document with `<ftp://…>` or bare `mailto:` links needs to know
those are recognised but not validated, and that `www.` links are
checked over `http`. The `elements` rule's element-name table and the
parser feature description also change with the rename.

## Open Questions

## Comments

### 2026-09-14T00:00:00+00:00

Author: program-manager

    Surfaced during triage of PR #44, which proposed narrowing the
    regex rather than removing the branch. That fix was verified
    incomplete: `\_my\_file.md` and `\_x\_.json` still false-positive
    under it, and extensionless backslash paths became silently
    undetected.

    The removal was verified in a throwaway worktree before this issue
    was written. Deleting `|\\` from the pattern clears all five prose
    cases above, leaves `./appendix.md` extraction intact, and produces
    exactly one test failure — `test_bare_link_backslash`, the test
    asserting the behaviour being removed. 843 passed, 1 failed, 50
    skipped.

### 2026-09-18T12:15:00+00:00

Author: program-manager/software-engineering

    Scoping. Verified every acceptance criterion against the code and
    specification: `RE_URL` carries the `|\\` alternative at
    `link.py:22`; both named tests exist in `test_link.py`; the spec
    sentence and the stale Pattern Reference block are where the
    criteria say. Criterion 4 was corrected — the mid-word test has no
    docstring to update, so the criterion now asks for one to be added.
    A Public Contract subsection was written out so acceptance tests
    can be authored without reading the implementation, and both
    scoping seeds are recorded under Design Decisions.

    Awaiting user approval of the scope and contract before acceptance
    test design begins.

### 2026-09-18T13:00:00+00:00

Author: program-manager/software-engineering

    Scoping reopened at the user's direction before approval. The
    user's goal is 1:1 parity with GFM link identification; removing
    the backslash branch alone was judged a half-measure that would be
    redone. Scope expanded from `bare-link-backslash-collision` to the
    whole of GFM 0.29 §6.5 Autolinks and §6.9 Autolinks (extension),
    covering `BracketLink` and `BareLink`, plus the `links` rule change
    that parity forces. Issue renamed to `autolink-gfm-parity` and the
    branch with it; `gfm-parity` tag added since this delivers two of
    the register's element entries.

    The specification text was read directly (cmark-gfm `test/spec.txt`,
    version 0.29; examples 602–631). One correction to earlier
    discussion: 0.29 has no bare `mailto:`/`xmpp:` protocol autolinks,
    so those are not in scope.

    Summary, Public Contract, Acceptance Criteria, and Design Decisions
    rewritten. Two Open Questions are held for the scoping approval
    gate. Awaiting user approval.

### 2026-09-18T13:30:00+00:00

Author: program-manager/software-engineering

    Correction to the previous comment. The user pasted §6.8 and §6.9
    from the published site, which is newer than the `cmark-gfm`
    `test/spec.txt` read earlier despite the same 0.29 version string.
    The site drops `ftp://` from extended URL autolinks and adds the
    extended protocol autolinks `mailto:` and `xmpp:` (examples
    633–635). The site numbers these sections 6.8 and 6.9 and the
    examples 603–635 — 33 in total. The Summary, Public Contract,
    Acceptance Criteria, and Design Decisions are updated to the site's
    numbering and rules; the site is recorded as the authority. Still
    awaiting user approval.

### 2026-09-18T14:00:00+00:00

Author: program-manager/software-engineering

    Scoping approved by the user. Framing settled as autolinks,
    traditional and extended — the syntax that visibly broke for a
    user — with inline links and the rest of the register deferred.
    Both Open Questions resolved and moved to Design Decisions:
    boundary is `Autolink` + `ExtendedAutolink` per §6.8/§6.9; the
    `links` rule validates `http`/`https` only.

    One addition at the gate: the user asked whether tiredize's element
    names match the specification's. They do not for these two, so the
    rename to `Autolink`/`ExtendedAutolink` (config `autolink`/
    `autolink_extended`) is folded in, recorded as a breaking change to
    the `elements` vocabulary with no alias. The four other non-GFM
    element names are noted for a separate rename issue.

    Proceeding to step 2, acceptance test design. The qa-engineer is
    given the published specification (HTML, examples 603–635) and a
    verified plain-text extract of §6.8–§6.9.

### 2026-09-18T13:10:41+00:00

Author: qa-engineer/software-engineering/testing

    Acceptance test design. 104 black-box tests written against the
    Public Contract and the published specification extract
    (examples numbered 603–635 as on the site). Nothing under
    `tiredize/` was touched; no existing test was changed.

    Files:

    - `tests/markdown/types/test_link_gfm_autolinks.py` (new, 63
      tests): the 33 spec examples, the preceding-character rule, the
      escape and relative-path negatives, position, and sanitize.
      A sibling of `test_link.py` rather than an addition to it,
      because the examples are the in-repo record of the spec and
      would otherwise double that module. `Autolink` and
      `ExtendedAutolink` are imported inside two helpers so that
      collection succeeds and each test fails on its own.
    - `tests/linter/rules/test_links.py` (+23): `links` rule.
    - `tests/linter/rules/test_elements.py` (+10): `disallow`.
    - `tests/linter/rules/test_line_length.py` (+4) and
      `tests/linter/rules/test_unicode.py` (+4): `exclude`.

    Criteria to tests:

    1. Examples 603–635 — `test_example_603_…` through
       `test_example_635_…`, one test per example, every paragraph
       of 624, 625, 627, 629, 632, 633, 634 asserted. 620 and 621
       assert `autolinks(text) == []` and exactly one extended
       autolink. Assertions compare the full list of `(string, url)`
       pairs, so extra matches fail as surely as missing ones.
    2. Preceding character — `test_extended_autolink_matches_after_
       delimiter` (4 delimiters × www/https) and
       `…_not_matched_after_letter_digit_or_quote` (3 × 2).
    3. Escapes and prose paths —
       `test_escape_sequences_are_not_extended_autolinks` (five
       cases incl. `\_dragon\_hoard.json`) and
       `test_relative_paths_in_prose_are_not_extended_autolinks`;
       end to end through the rule in
       `test_prose_paths_and_escapes_produce_no_finding`.
    4. Relative path validation unchanged —
       `test_inline_link_relative_path_{found,missing}` and
       `test_reference_definition_relative_path_{found,missing}`,
       real files under `tmp_path`, `check_url_valid` not mocked.
    5. `links` rule — `test_non_http_autolink_recognised_but_not_
       validated` (irc, ftp, unregistered, localhost, email, MAILTO)
       and `…_extended_autolink_…` (bare email, mailto, xmpp) read
       `Section.autolinks` / `Section.autolinks_extended` first so
       the silence is not vacuous; `test_www_extended_autolink_
       validated_over_http`, `…_finding_names_http_url`,
       `…_excluded_by_hostname`; `test_autolink_finding_names_
       element_autolink`, `test_extended_autolink_finding_names_
       element_extended_autolink`; `…_validated_without_trailing_
       punctuation`.
    6. Sanitize — `test_autolink_sanitize_blanks_exactly_the_
       bracketed_span`, `…_leaves_non_autolinks_alone`,
       `test_extended_autolink_sanitize_stops_before_trailing_
       punctuation`, `…_keeps_unmatched_closing_paren`,
       `…_matches_extract_spans` (expected text derived from
       `extract()` positions), `…_leaves_plain_text_alone`.
    7. `elements` vocabulary — `test_disallow_autolink_flags_each_
       scheme` (https, irc, email), `test_disallow_autolink_
       extended_flags_each_form` (https, www, email, mailto),
       `…_does_not_flag_extended_autolink`, `test_disallow_rejects_
       old_link_names`; and for `exclude`, `test_exclude_autolink_
       …`, `test_exclude_autolink_extended_…`, `test_exclude_
       rejects_old_link_names` in both `test_line_length.py` and
       `test_unicode.py`.

    Interpretation recorded for the gate: the `elements` rule has no
    `exclude` key. `exclude` element lists live on `line_length` and
    `unicode`, and the README documents one vocabulary "valid in
    `exclude` and `disallow` lists". Criterion 7's `exclude` is
    tested there. The old-name rejection asserts the full message
    `Unknown element name in disallow: '…'` (or `exclude`) that the
    contract names.

    Pre-skip evidence (markers stripped, `python3 -m pytest` on the
    five files): 100 failed, 4 passed. Full suite: 100 failed, 848
    passed, 50 skipped. By reason:

    - 63 ImportError `cannot import name 'Autolink'` (22) /
      `'ExtendedAutolink'` (41) — every test in the new module;
      name does not exist yet.
    - 9 AttributeError `'Section' object has no attribute
      'autolinks'` (6) / `'autolinks_extended'` (3) — name does not
      exist yet.
    - 12 ValueError `Unknown element name in disallow/exclude:
      'autolink'` / `'autolink_extended'` — config-load rejection of
      the new vocabulary.
    - 16 assertion failures against the contract: 6 `DID NOT RAISE`
      for `link_bare` / `link_bracket` still accepted; 4 findings
      for `./configure`, `../guide.md`, `\*.dll`, `\\server\share`;
      finding messages still say "Bracket link" / "Bare link";
      `www.` never checked (call count 0, finding count 0);
      trailing `.` handed to `check_url_valid`.
    - 4 pass today and stay unskipped: the relative-path guards.

    To show the new module would fail on assertions and not only on
    import, it was also run once with the new names aliased in
    memory to today's `BracketLink` / `BareLink` (a scratch script,
    nothing committed): 43 of 63 failed on assertions, 20 passed
    where today's behaviour already agrees with GFM (603, 604, 609,
    611, 612, 615–620, and the https halves of the preceding-
    character tests). Every failure was an assertion.

    Skip marker step 3 must remove, present on the 100 failing
    tests: `@pytest.mark.skip(reason=PENDING)` with module constant
    `PENDING = "autolink-gfm-parity: awaiting implementation
    (step 3)"` in each of the five files. With markers in place:
    flake8 clean; 848 passed, 150 skipped; the pre-commit hook
    passes.

    Not asserted, deliberately: whether `< http://foo.bar >` (617)
    yields an extended autolink. The §6.8 examples are rendered
    without the extension, so their HTML is silent on §6.9; the
    contract's rules say it does, and the criteria mandate the
    dual assertion only for 620 and 621. Step 3 may add it as an
    edge test if the user wants it pinned.

### 2026-09-18T14:30:00+00:00

Author: program-manager/software-engineering

    Step-2 gate, first pass. The user reviewed the 104-test suite and
    ruled on the two flags: (1) criterion 7's `exclude` on `elements`
    was a scoping error — corrected to `disallow` on `elements` and
    `exclude` on `line_length`/`unicode`, matching what the
    qa-engineer tested; no new `exclude` option is added. (2) Example
    617 must also assert its §6.9 half explicitly — the user wants
    every specification example pinned by a unit test, both halves
    where both apply. Criterion 1 amended. Routing back to the
    qa-engineer for that one addition before approval is recorded.

### 2026-09-18T13:21:07+00:00

Author: qa-engineer/software-engineering/testing

    Step-2 revision per the gate ruling on example 617.
    `test_example_617_spaces_around_uri_inside_brackets` in
    `tests/markdown/types/test_link_gfm_autolinks.py` is extended in
    place, in the same shape as 620 and 621: it still asserts
    `autolinks(text) == []` and now also asserts
    `extended_autolinks("< http://foo.bar >") ==
    [("http://foo.bar", "http://foo.bar")]`, with a docstring giving
    the reason — `http://foo.bar` follows whitespace, so it qualifies
    under §6.9 even though the bracketed form fails §6.8. Criterion 1
    is now covered as amended. No other file changed.

    Pre-skip evidence: with the marker removed the test fails on
    `ImportError: cannot import name 'Autolink'`, the same reason as
    the rest of the module. With the new names aliased in memory to
    today's `BracketLink` / `BareLink` (scratch copy, nothing
    committed) the test passes: today's `BareLink` already matches
    `http://foo.bar` after whitespace with `string == url`, so the
    §6.9 half pins existing agreement with GFM rather than a change,
    as 615–620 did before.

    Marker restored: `@pytest.mark.skip(reason=PENDING)`. flake8
    clean; full suite 848 passed, 150 skipped (unchanged, since no
    test was added). Ready for the gate.

### 2026-09-18T15:00:00+00:00

Author: program-manager/software-engineering

    Approval point 2 passed. The user approved the acceptance test
    suite as the definition of correct: 104 tests, every specification
    example 603–635 pinned, both halves where both apply. Routing to
    step 3, implementation.

### 2026-09-18T13:57:33+00:00

Author: software-engineer/software-engineering/git,python,testing

    Implementation. Four code commits, one per criterion group, each
    green under the local flake8 + pytest hook:

    - d3ffc90 rename (criterion 1): classes, `Section` fields,
      elements vocabulary and labels, `links` rule messages; every
      existing test moved to the new names; the rename-only
      acceptance tests unskipped.
    - 137e4ee `Autolink` per 6.8 (criterion 2): examples 603-620
      and the Autolink position/sanitize tests unskipped;
      `test_autolink_ftp` / `test_autolink_email` lose their
      gfm-parity skips.
    - d8d6baf `ExtendedAutolink` per 6.9 (criteria 3, 4, 7 and the
      rest of 6): every remaining parser-side acceptance test
      unskipped; `test_extended_autolink_backslash_path_is_not_a_link`
      (inverted, renamed) and the mid-word registry-key test (renamed
      vocabulary, docstring added); `./` and `../` tests inverted;
      `test_extended_autolink_trailing_punctuation_stripped` unskipped;
      `test_extended_autolink_www` removed as superseded by examples
      622/623 -- its `url == "www.example.com"` assertion predates
      the `http://` normalisation, so it could not be unskipped.
    - 42c7234 `links` rule scheme gate (criterion 5): last nine
      acceptance tests unskipped.

    Final state: `python3 -m pytest -q` 1063 passed, 46 skipped
    (the 46 are the pre-existing gfm-parity register skips, down from
    50); flake8 clean; zero `PENDING` markers or constants. Coverage
    of changed source: `tiredize/markdown/types/link.py` 162
    statements, 100%; `tiredize/linter/rules/links.py` 96, 100%;
    `_elements.py` and `section.py` unchanged in coverage (section.py
    line 167 was uncovered before this issue and is untouched).
    Whole package 99%.

    How it is built. `Autolink` is one VERBOSE regex with a URI
    branch (2-32 char scheme, `[^\x00-\x20\x7F<>]*`) tried before
    the HTML5 email branch. `ExtendedAutolink` is a candidate regex
    plus a Python pass: `RE_CANDIDATE` anchors on the preceding-
    character rule and captures the longest run each of the four
    forms allows; `_validate_url` checks the domain (`RE_DOMAIN`
    prefix, at least one `.`, no `_` in the last two segments) and
    hands the run to `_trim`, which loops from the end applying the
    three path-validation rules exactly as the contract lists them;
    `_validate_email` rejects a domain ending in `-`/`_` outright and
    keeps a `/resource` only for `xmpp:`. Email domains and xmpp
    resources are written as non-empty `.`-joined segments, so a
    trailing `.` falls outside the match by construction rather than
    by trimming. `_scan` resumes one character after a rejected
    candidate (so `http://nodot(www.a.b)` still yields `www.a.b`)
    and at the trimmed end of an accepted one. Both `sanitize()`
    methods blank the spans `extract()` reports, via a module-level
    `_blank_spans`. The `links` rule gains `_has_checkable_scheme`:
    a regex scheme parse (not urlparse, which raises on `http://[::1`)
    returning True for no scheme or http/https in any case.

    Contract interpretations -- please read these, reviewers:

    1. "No reference to the old names remains in tiredize/ or
       tests/" cannot be literally true: the approved acceptance
       tests quote `link_bare` / `link_bracket` to assert they are
       rejected (`test_*_rejects_old_link_names` in three files, and
       two header comments). Those are the only residual grep hits;
       nothing else in either tree names the old identifiers.
    2. `sanitize()` is implemented as "blank the spans extract()
       reports", the contract's literal words. Consequence: a
       bracketed URI inside inline code is no longer blanked by
       `Autolink.sanitize()`. No caller can observe this -- the only
       in-package caller is `ExtendedAutolink.extract`, which has
       already blanked code -- and it makes the two methods
       consistent with each other and the acceptance test that
       derives the expected text from `extract()` positions.
    3. "Alphanumeric" is read as Unicode alphanumeric (`\w`) in
       domains, local parts and resources, so `www.bücher.example`
       and `josé@b.c` link. cmark-gfm is Unicode-aware for www/url
       domains and ASCII-only for emails; one reading was chosen for
       both and pinned in white-box tests.
    4. The `http://`/`https://` prefix of an extended url autolink is
       matched case-insensitively, as cmark-gfm does (`HTTP://a.b`
       links on GitHub); `mailto:`/`xmpp:` are case-sensitive, as
       the spec writes them and cmark-gfm compares them. `string`
       and `url` keep the scheme as written; the `links` rule lowers
       it when gating.
    5. The preceding-character rule is applied to all four extended
       forms, as the contract states. cmark-gfm applies it only to
       `www.`; a bare email after `"` or `/` links on GitHub but not
       here. The acceptance tests pin the contract's version.
    6. The `links` rule gate applies to every link kind, not only
       autolinks: an inline link or reference definition with a
       `mailto:`/`ftp:` target now produces no finding either (it was
       a guaranteed false positive before). Scheme-less targets --
       anchors, `./` paths, and `[x](example.com)` -- still go to
       `check_url_valid` exactly as before, so its anchor and
       relative branches are unchanged in behaviour and in code.
    7. Contract-vs-cmark-gfm divergences implemented per the
       contract and pinned in `test_link.py` with a comment, for the
       PM to weigh (each is a one-line change if the contract is
       amended): (a) a lone trailing `;`, `'` or `"` is kept -- the
       contract's punctuation list is closed and omits them, cmark-gfm
       strips all three, so `see www.a.b/x;` validates `.../x;` here
       but links `.../x` on GitHub; (b) `http://localhost/x` is not a
       link because the contract requires a period in the domain,
       while cmark-gfm's url matcher allows a dot-less domain; (c) an
       email whose domain ends in a digit links here per the
       contract's "last character must not be `-` or `_`", while
       cmark-gfm requires a letter or `.`; (d) `xmpp:a@b.c/` links as
       `xmpp:a@b.c` here; cmark-gfm produces no link at all for a
       trailing empty resource, which reads as a bug there.

    Out of scope, noted for the PM: `_is_excluded` in the `links`
    rule calls `urlparse().hostname`, which raises ValueError on a
    malformed URL such as `http://[::1` when `exclude` is configured
    (pre-existing; the new gate deliberately avoids urlparse for that
    reason). A smoke run of both extractors over README.md and this
    issue file found one extended autolink: `http://foo.bar` inside a
    backtick span that crosses a line break, which `CodeInline` does
    not recognise -- a `CodeInline` register item, not an autolink
    false positive. The acceptance-test header comment in
    `tests/linter/rules/test_links.py` still says the `Section`
    fields "do not exist until step 3"; left untouched under the
    step boundary.

    Notes for later steps: the parser specification's Pattern
    Reference should show `RE_AUTOLINK` and `RE_CANDIDATE` +
    `_trim`, not a single extended pattern -- the extended rules are
    procedural by design. The README `links` section should say that
    only http/https targets are checked for every link kind, and
    that `www.` links are checked over `http://`.

### 2026-09-18T16:15:00+00:00

Author: program-manager/software-engineering

    Post-step-3 review with the user of the engineer's contract
    interpretations. Decided and recorded under Design Decisions:
    the specification is followed concretely with cmark-gfm as the
    tie-break where it is silent; the links scheme gate is uniform;
    out-of-scope defects become skipped regression tests naming a
    filed issue. Two consequences route back to step 3 as a revision:
    email "alphanumeric" becomes ASCII (domains stay Unicode), and a
    skipped regression test is added for the `_is_excluded()` crash,
    referencing the new draft issue `links-exclude-malformed-url-crash`.
    Step 4 begins once the revision lands.

### 2026-09-18T14:42:46+00:00

Author: software-engineer/software-engineering/git,python,testing

    Step-3 revision per the 16:15 routing. Two code commits, each
    green under the local flake8 + pytest hook; interpretations 4, 5
    and 6a untouched; no step-2 acceptance test changed.

    - 553f25c email alphanumerics become ASCII. In
      `tiredize/markdown/types/link.py` the email alternative of
      `RE_CANDIDATE` now uses `[A-Za-z0-9]` for the local part, the
      domain segments and the xmpp resource, for the bare, `mailto:`
      and `xmpp:` forms alike; `RE_DOMAIN` (www/http domains) keeps
      `\w`. The class docstring and the pattern comments say which is
      which and why (cmark-gfm: `isalnum` for emails, Unicode-aware
      host check for domains). In `tests/markdown/types/test_link.py`,
      `test_extended_autolink_email_may_be_non_ascii` became
      `test_extended_autolink_email_must_be_ascii` (`josé@example.com`
      and `jose@exämple.com` yield nothing; `jose@example.cöm` yields
      `jose@example.c`), `test_extended_autolink_domain_may_be_non_
      ascii` now also pins `www.münchen.de` and `https://münchen.de/x`
      and says emails differ, and two tests were added:
      `test_extended_autolink_protocol_address_must_be_ascii`
      (`mailto:`/`xmpp:` with a non-ASCII local part or domain) and
      `test_extended_autolink_xmpp_resource_must_be_ascii`
      (`xmpp:a@b.c/ré` links as `xmpp:a@b.c/r`; `xmpp:a@b.c/é` as
      `xmpp:a@b.c`). Coverage of `link.py` stays 162/162.

      One point worth a reviewer's eye: a non-ASCII character inside
      an email *domain* does not void the address, it ends it, so
      `jose@example.cöm` links as `jose@example.c` and `xmpp:jose@b.cé`
      as `xmpp:jose@b.c`. That is the same rule `/`, `?` and `_` in a
      resource already follow (`a@b.c/d` links as `a@b.c`), it is what
      cmark-gfm's byte scanner does (it breaks at the first
      non-`isalnum` byte and links what precedes it), and it is what
      the contract's grammar produces. My first draft of the test
      asserted "no link at all" from a wrong assumption; the code was
      right and the test was corrected, not the code. Before the `@`
      a non-ASCII letter does void the address, because it breaks the
      local part and `é` is not a valid preceding character.

    - f0173fd skipped regression test for the `_is_excluded` crash.
      `test_malformed_url_with_exclude_configured_is_a_finding_not_a_
      crash` in `tests/linter/rules/test_links.py`: `<http://[::1>`
      with `{"validate": True, "exclude": ["*.example.com"]}`,
      `check_url_valid` mocked to `(False, None, "invalid url")`,
      asserting one call, one finding, `http://[::1` in its message.
      Run unskipped first: it fails with `ValueError: Invalid IPv6
      URL`, raised at `/usr/lib/python3.13/urllib/parse.py:514` in
      `urlsplit`, via `urlparse` from `_is_excluded`
      (`tiredize/linter/rules/links.py:65`), reached from the
      autolink loop in `validate` (`links.py:171`). Then marked
      `@pytest.mark.skip(reason="links-exclude-malformed-url-crash:
      _is_excluded raises on URLs urlparse cannot parse")`. The crash
      is not fixed; the draft issue owns it.

    Final state: `python3 -m pytest -q` 1065 passed, 47 skipped;
    flake8 clean; package coverage 99%, `link.py` and `links.py`
    100%. The passed count is 1065 rather than the 1063 the routing
    anticipated because the two protocol/resource ASCII tests are
    new; the 47th skip is the regression test above. The issue file
    is committed separately as a third commit.
