# Rule: links

## Overview

The `links` linter rule (`tiredize/linter/rules/links.py`). Checks that link targets resolve: anchors against the document's headings, `.`-relative paths against the file system, and `http`/`https` targets with an HTTP request. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key                  | Type   | Required | When absent                    | Accepted values |
|----------------------|--------|----------|--------------------------------|-----------------|
| `validate`           | `bool` | yes      | —                              | `false` turns the rule off while leaving it configured |
| `exclude`            | `list` | no       | nothing excluded               | Hostname glob patterns (`*.example.com`); strings only |
| `headers`            | `dict` | no       | `User-Agent: tiredize-link-checker/1.0` | HTTP headers sent with every request; a non-empty mapping replaces the default entirely |
| `timeout`            | `int`  | no       | no timeout: a request waits as long as the server takes | Seconds |
| `valid_status_codes` | `list` | no       | every 2xx and 3xx              | Integers, or class wildcards `Nxx` (`2xx`, case-insensitive); a boolean or anything else raises `ValueError` |

## Behaviour

Checks the targets of inline links, autolinks, extended autolinks and
reference definitions with `check_url_valid()` (see [linter
engine](./linter-engine.md)). Reference-style links and images are not
checked. Redirects are always followed and TLS certificates are always
verified; neither is configurable. An empty `valid_status_codes: []`
accepts no status at all, so every HTTP link is reported. Two gates
decide what is checked.

### Scheme Gate

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

### Exclusion Gate

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

## Open Questions

- `links.timeout` has no default, so an unresponsive host can stall a run indefinitely.
- `valid_status_codes: []` makes every HTTP link fail; it is accepted rather than rejected.
