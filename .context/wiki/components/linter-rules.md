# Linter Rules

## Overview

The built-in rules in `tiredize/linter/rules/`, what each checks,
and the configuration each accepts. A rule runs only when the rules
file has an entry for it. How rules are discovered, how their
configuration is checked, and the element vocabulary their `exclude`
and `disallow` lists use are on the [linter engine](./linter-engine.md)
page.

Every finding carries a position (character offset and length) that the
[CLI](./cli.md) turns into `line:col`.

## Contracts and Interfaces

| Rule                  | Required keys    | Optional keys                                          |
|-----------------------|------------------|--------------------------------------------------------|
| `elements`            | `disallow`       | —                                                      |
| `line_length`         | `maximum_length` | `exclude`                                              |
| `links`               | `validate`       | `exclude`, `headers`, `timeout`, `valid_status_codes`  |
| `tabs`                | —                | `allowed`                                              |
| `trailing_whitespace` | —                | `allowed`                                              |
| `unicode`             | `allowed`        | `exclude`                                              |

`tabs.allowed` and `trailing_whitespace.allowed` are optional because
both rules still forbid their target with the key absent.
`unicode.allowed` is required because it selects the mode the rule runs
in. `elements: {disallow: []}` is legal and allows everything.

## elements

Reports each occurrence of an element type named in `disallow`, as
`<Label> is not allowed.` at the element's position. Elements with an
empty span are skipped. An unknown name raises `ValueError`.

## line_length

Reports a line longer than `maximum_length` characters, measured in
Unicode characters with the line ending removed. The finding covers the
overflow, from `maximum_length` to the end of the line. A line that
overlaps any element named in `exclude` is exempt as a whole.

## tabs

Reports each tab character, one finding per tab, unless `allowed` is
true.

## trailing_whitespace

Reports whitespace before the line ending, one finding per line
covering the whole run, unless `allowed` is true.

## unicode

Reports each non-ASCII character (code point above 127) where it is not
permitted. With `allowed: false`, non-ASCII is forbidden everywhere
except inside the elements named in `exclude`. With `allowed: true`, it
is permitted everywhere except inside those elements. The message names
the character and its code point.

## links

Checks the targets of four kinds of link with `check_url_valid()`:
inline links, autolinks, extended autolinks and reference definitions.
Reference-style links and images are not checked. `validate: false`
returns no findings. Two gates decide what is checked.

### Scheme gate

Only `http` and `https` targets are checked. The leading scheme is read
with `[A-Za-z][A-Za-z0-9+.-]*:`, the token urllib would split off,
rather than with `urlparse`:

- no scheme (`#anchor`, `./file.md`, `example.com`): checked, so anchors
  and `.`-relative paths are resolved locally and `example.com` is
  reported as "No scheme supplied";
- `http` or `https` in any letter case: checked;
- any other scheme: skipped with no finding.

"Any other scheme" is judged by shape, not by a list: `mailto:`,
`xmpp:`, `irc:`, `ftp:` and unregistered schemes such as `a+b+c:` are
skipped, and so is any target whose first token parses as a scheme,
such as `localhost:8080`, `example.com:8080/x` or `C:\path`. The parser
has already normalised `url`, so a `www.` extended autolink is checked
as `http://www.…` and a bare email arrives as `mailto:…` and is
skipped.

### Exclusion gate

`exclude` holds hostname glob patterns. `urlparse(url).hostname` is
matched against each pattern with `fnmatch`, both in lower case; a URL
with no hostname is never excluded. Exclusion is judged after the scheme
gate. When `exclude` is set, a URL that `urlparse` cannot parse (such as
`http://[::1`) raises `ValueError`, which stops the run as a runtime
error.

### Other options

`timeout` (seconds) and `headers` are passed to the request.
`valid_status_codes` lists exact codes or class wildcards (`2xx`); any
other entry, including a boolean, raises `ValueError`. Without it, every
2xx and 3xx is valid. Redirects are followed.

### Findings

One finding per failed check, at the element's position:
`Inline link '…' is not reachable.`, `Autolink '…'`, `Extended autolink
'…'` or `Reference link '…'`, each followed by `Status code: …, Error:
…`.

## Design Decisions

- **The `links` rule checks only what it can check, the same way for
  every link kind.** The parser recognises every scheme GFM does, but a
  non-HTTP target can only ever be reported unreachable by an HTTP
  request, which would be a larger false-positive class than GFM parity
  removed. The gate applies to inline links and reference definitions
  too, so `[text](mailto:…)` and `[ref]: ftp://…` produce no guaranteed
  false positive. Other schemes stay links for the `elements` rule.
- **The scheme is parsed with a regex, not `urlparse`,** so a malformed
  URL cannot raise before `check_url_valid()` reports it.
- **Windows paths are not validated.** Supporting them would need a
  feature design, not a pattern that can only produce errors.
