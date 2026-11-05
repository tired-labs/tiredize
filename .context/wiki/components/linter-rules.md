# Linter Rules

## Overview

The contract for every built-in rule in `tiredize/linter/rules/`: the
configuration keys it accepts, their types, defaults and accepted
values, and what the rule reports. The README's rule tables are the
user-facing version of this page.

How rules are discovered, how a configuration block is checked before a
rule runs, and the element vocabulary used by `disallow` and `exclude`
are on the [linter engine](./linter-engine.md) page. Every finding
carries a position (character offset and length) that the
[CLI](./cli.md) turns into `line:col`.

## Contracts and Interfaces

### Rules File

The file passed with `--rules` is a YAML mapping from rule id to that
rule's configuration mapping. A rule runs only when it has an entry.

```yaml
line_length:
  maximum_length: 80
  exclude: [code_block, table]
tabs: {}
links:
  validate: true
  timeout: 10
```

A rule that needs no keys is enabled with an empty mapping (`tabs: {}`);
an entry with nothing under it (`tabs:`) is YAML null and is a runtime
error. Every key below is checked by `validate_config()` before the rule
runs: an unknown key, a wrong type or a missing required key stops the
run (see [linter engine](./linter-engine.md)). "Type" uses that
function's vocabulary: `bool`, `int` (never a boolean), `list`, `dict`.

### Rules at a Glance

| Rule                  | Required keys    | Optional keys                                         |
|-----------------------|------------------|-------------------------------------------------------|
| `elements`            | `disallow`       | —                                                     |
| `line_length`         | `maximum_length` | `exclude`                                             |
| `links`               | `validate`       | `exclude`, `headers`, `timeout`, `valid_status_codes` |
| `tabs`                | —                | `allowed`                                             |
| `trailing_whitespace` | —                | `allowed`                                             |
| `unicode`             | `allowed`        | `exclude`                                             |

## elements

| Key        | Type   | Required | When absent | Accepted values                              |
|------------|--------|----------|-------------|----------------------------------------------|
| `disallow` | `list` | yes      | —           | Element vocabulary names; `[]` allows everything |

Reports each occurrence of a disallowed element type as `<Label> is
not allowed.` at the element's position. Elements with an empty span
are skipped. A non-string entry or an unknown name raises `ValueError`.

## line_length

| Key              | Type   | Required | When absent     | Accepted values          |
|------------------|--------|----------|-----------------|--------------------------|
| `maximum_length` | `int`  | yes      | —               | Any integer; no bound is checked |
| `exclude`        | `list` | no       | no exemptions   | Element vocabulary names |

Reports a line longer than `maximum_length` characters, counted in
Unicode code points with the line ending removed. The finding covers
the overflow, from `maximum_length` to the end of the line. A line that
overlaps any element named in `exclude`, even partly, is exempt as a
whole. A non-string entry or an unknown name in `exclude` raises
`ValueError`.

## links

| Key                  | Type   | Required | When absent                    | Accepted values |
|----------------------|--------|----------|--------------------------------|-----------------|
| `validate`           | `bool` | yes      | —                              | `false` turns the rule off while leaving it configured |
| `exclude`            | `list` | no       | nothing excluded               | Hostname glob patterns (`*.example.com`); strings only |
| `headers`            | `dict` | no       | `User-Agent: tiredize-link-checker/1.0` | HTTP headers sent with every request; a non-empty mapping replaces the default entirely |
| `timeout`            | `int`  | no       | no timeout: a request waits as long as the server takes | Seconds |
| `valid_status_codes` | `list` | no       | every 2xx and 3xx              | Integers, or class wildcards `Nxx` (`2xx`, case-insensitive); a boolean or anything else raises `ValueError` |

Checks the targets of inline links, autolinks, extended autolinks and
reference definitions with `check_url_valid()` (see [linter
engine](./linter-engine.md)). Reference-style links and images are not
checked. Redirects are always followed and TLS certificates are always
verified; neither is configurable. An empty `valid_status_codes: []`
accepts no status at all, so every HTTP link is reported. Two gates
decide what is checked.

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

`urlparse(url).hostname` is matched against each `exclude` pattern with
`fnmatch`, both in lower case; a URL with no hostname (an anchor or a
relative path) is never excluded. Exclusion is judged after the scheme
gate. When `exclude` is set, a URL that `urlparse` cannot parse (such as
`http://[::1`) raises `ValueError`, which stops the run as a runtime
error.

### Findings

One finding per failed check, at the element's position:
`Inline link '…' is not reachable.`, `Autolink '…'`, `Extended autolink
'…'` or `Reference link '…'`, each followed by `Status code: …, Error:
…`.

## tabs

| Key       | Type   | Required | When absent     | Accepted values |
|-----------|--------|----------|-----------------|-----------------|
| `allowed` | `bool` | no       | tabs forbidden  | `true` permits tabs, which makes the rule check nothing |

Reports each tab character, one finding per tab.

## trailing_whitespace

| Key       | Type   | Required | When absent                   | Accepted values |
|-----------|--------|----------|-------------------------------|-----------------|
| `allowed` | `bool` | no       | trailing whitespace forbidden | `true` permits it, which makes the rule check nothing |

Reports whitespace (any character `str.isspace()` accepts) before the
line ending, one finding per line covering the whole run.

## unicode

| Key       | Type   | Required | When absent   | Accepted values          |
|-----------|--------|----------|---------------|--------------------------|
| `allowed` | `bool` | yes      | —             | `true` or `false`; selects the mode |
| `exclude` | `list` | no       | no exemptions | Element vocabulary names |

Reports each non-ASCII character (code point above 127) where it is not
permitted. With `allowed: false`, non-ASCII is forbidden everywhere
except inside the elements named in `exclude`. With `allowed: true`, it
is permitted everywhere except inside those elements. The message names
the character and its code point. A non-string entry or an unknown name
in `exclude` raises `ValueError`.

## Design Decisions

- **Required keys are the ones without which a rule would be inert**
  (see [linter engine](./linter-engine.md)). `tabs.allowed` and
  `trailing_whitespace.allowed` are optional because both rules still
  forbid their target with the key absent; `unicode.allowed` is required
  because it selects the mode the rule runs in.
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

## Open Questions

- `links.timeout` has no default, so an unresponsive host can stall a run indefinitely.
- `tabs.allowed: true` and `trailing_whitespace.allowed: true` leave an enabled rule checking nothing, which the "never a no-op" principle forbids for omitted keys but not for these values.
- `valid_status_codes: []` makes every HTTP link fail; it is accepted rather than rejected.
