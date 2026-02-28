Status: draft

# Handle relative URLs without dot prefix in check_url_valid

## Summary

`check_url_valid()` only recognizes relative file paths that start with
`.` (e.g., `./foo.md`, `../bar.md`). A relative URL like `sibling.md`
(no leading dot) falls through to the HTTP validation branch, where
`requests.get()` fails with a `MissingSchema` or `RequestException`.
The function returns `(False, None, "<exception text>")` instead of
resolving the path as a local file.

Discovered during peer review of `fix-relative-url-resolution.md`.

## Acceptance Criteria

- [ ] Define which URL patterns should be treated as relative file
      paths (e.g., no scheme, no leading `#`, not starting with `.`)
- [ ] Update `check_url_valid()` to resolve these patterns as local
      files against `document.path.parent`
- [ ] Unit tests cover: bare filename (`sibling.md`), subdirectory
      path (`sub/file.md`), and paths that look relative but aren't
      (e.g., `mailto:`, `ftp://`)
- [ ] Linter specification updated to document the full set of
      recognized URL patterns

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Anchor validation (`#` URLs)
- HTTP/HTTPS URL validation
- Existing `./` and `../` relative path handling (already fixed)

## Design Decisions

## Open Questions

- What heuristic should distinguish a bare relative path from other
  non-HTTP URL schemes? Should we check for the presence of `://` or
  maintain an explicit allowlist of recognized schemes?
