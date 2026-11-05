# Rule: links

## Overview

The `links` linter rule (`tiredize/linter/rules/links.py`). Checks that link targets resolve: anchors against the document's headings, `.`-relative paths against the file system, and `http`/`https` targets with an HTTP request. How the rules file is shaped, how configuration is checked before a rule runs, and the element vocabulary are on the [linter engine](./linter-engine.md) page.

## Contracts and Interfaces

| Key                  | Type   | Required | When absent                    | Accepted values |
|----------------------|--------|----------|--------------------------------|-----------------|
| `validate`           | `bool` | yes      | —                              | `false` turns the rule off while leaving it configured |
| `exclude`            | `list` | no       | nothing excluded               | Hostname glob patterns (`*.example.com`); strings only |
| `headers`            | `dict` | no       | `User-Agent: tiredize-link-checker/1.0` | HTTP headers sent with every request; a non-empty mapping replaces the default entirely, and `{}` keeps it. Names and values are not checked (see Behaviour) |
| `timeout`            | `int`  | no       | no timeout: a request waits as long as the server takes | Whole seconds; a float such as `1.5` is rejected. `0` or a negative value is accepted here but raises at the first HTTP request (see Behaviour) |
| `valid_status_codes` | `list` | no       | every 2xx and 3xx              | Integers of any value, or class wildcards `Nxx` with `N` a digit (`2xx`, case-insensitive); a quoted number such as `'200'`, a boolean or anything else raises `ValueError` |

With `validate: false` the rule returns at once, so malformed `exclude`
or `valid_status_codes` entries are not reported; wrong key types still
are. With `validate: true` entries are checked before any link:

| Entry                                      | Error |
|--------------------------------------------|-------|
| Non-string `exclude` entry                 | `ValueError: exclude entries must be strings, got 'NoneType': None` (type name and `repr` of the entry) |
| Boolean `valid_status_codes` entry         | `ValueError: valid_status_codes entries must be integers or class wildcards like '2xx', got bool: True` |
| Any other bad `valid_status_codes` entry   | `ValueError: valid_status_codes entries must be integers or class wildcards like '2xx', got 'str': '200'` (type name and `repr` of the entry) |

## Behaviour

Checks the targets of inline links, autolinks, extended autolinks and
reference definitions with `check_url_valid()`; how anchors, relative
paths and HTTP targets are resolved, and the error strings it returns,
are under URL Checking on the [linter engine](./linter-engine.md) page.
Reference-style links, inline images and reference-style images are
not checked. Redirects are always followed and TLS certificates are
always verified; neither is configurable. An empty
`valid_status_codes: []` accepts no status at all, so every HTTP link is
reported.

Each occurrence is checked separately, one request at a time; a URL
that appears several times is fetched several times.

The rule sees only the links the [markdown parser](./markdown-parser.md)
extracts. In a document with headings, links before the first heading
are not checked. After frontmatter, the parser skips one character, so
a link starting on the line right after the frontmatter can be missed.

Two gates decide what is checked.

### Scheme Gate

Only `http` and `https` targets are checked. The leading scheme is read
with `[A-Za-z][A-Za-z0-9+.-]*:`, the token urllib would split off,
rather than with `urlparse`:

- no scheme (`#anchor`, `./file.md`, `docs/file.md`, `example.com`):
  checked, so anchors and `.`-relative paths are resolved locally, and
  anything else is sent as an HTTP request and reported with "No scheme
  supplied";
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
`fnmatch.fnmatchcase`, both in lower case. Only the hostname is
matched: ports and paths are ignored, and `*.example.com` matches
subdomains but not `example.com` itself, which needs its own entry. A
URL with no hostname (an anchor or a relative path) is never excluded.
Exclusion is judged after the scheme gate. When `exclude` is non-empty,
a URL that `urlparse` cannot parse (such as `http://[::1`) raises
`ValueError` ("Invalid IPv6 URL"), which stops the run as a runtime
error; with no `exclude` the same URL is reported as a finding.

### Request Errors

`headers` is passed to requests as it is. A header whose value is not
a string makes every HTTP link fail with requests' error text (`Header
part (1) from ('X', 1) must be of type str or bytes, …`); a header whose
value is null is left out of the request. A `timeout` of `0` or less
raises urllib3's `ValueError` ("Attempted to set connect timeout to 0,
but the timeout cannot be set to a value less than or equal to 0.") at
the first HTTP link, which stops the run.

### Findings

One finding per failed check, at the element's full span:

| Rule id | Message                                                                                         | Position |
|---------|-------------------------------------------------------------------------------------------------|----------|
| `links` | `<Kind> '<url>' is not reachable. Status code: <status>, Error: <error>`                         | The link element's span |

`<Kind>` is `Inline link`, `Autolink`, `Extended autolink` or
`Reference link`. `<url>` is the normalised target. `<status>` is the
HTTP status, or `None` when no response arrived; `<error>` is
`check_url_valid()`'s error string, or `None` for an HTTP response.
Examples:

- `Inline link 'http://x.y' is not reachable. Status code: 404, Error: None`
- `Inline link '#nope' is not reachable. Status code: None, Error: anchor not found in document`
- `Autolink 'http://x.y' is not reachable. Status code: None, Error: timeout`

Within a section, findings are grouped by kind (inline links, then
autolinks, extended autolinks and reference definitions), each in the
parser's order; they are not sorted by position.

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
