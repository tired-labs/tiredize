# Specification: BracketLink

**GFM Equivalent:** Autolinks (GFM spec section 6.5)
**Source File:** `tiredize/markdown/types/link.py`
**GFM Compliance:** Partial

## Description

A bracket link (autolink) is a URL enclosed in angle brackets:
`<https://example.com>`. The parser only matches absolute HTTP/HTTPS
URLs.

## Dataclass Fields

| Field | Type | Description |
|-------|------|-------------|
| `position` | `Position` | Character offset and length relative to document root |
| `string` | `str` | The full matched text including angle brackets |
| `url` | `str` | The URL between the angle brackets |

## Regex Pattern

```
<                            # Opening angle bracket
(?P<url>https?:\/\/\S+)     # URL: must start with http:// or https://
>                            # Closing angle bracket
```

Only matches absolute HTTP/HTTPS URLs. The `\S+` after the scheme
captures any non-whitespace characters.

## Sanitization

**Chain (in order):** CodeBlock, CodeInline
**Own sanitize():** Replaces entire match (brackets + URL) with
whitespace, preserving character offsets. Used by BareLink's
sanitization chain.

## GFM Compliance

Partial compliance with GFM spec section 6.5. Known gaps:

- Non-HTTP schemes (`<ftp://example.com>`, `<mailto:user@host>`)
  not matched. Pattern requires `https?://`.
- Email autolinks (`<user@example.com>`) not matched.

## Naming

| Internal | GFM Spec Term |
|----------|---------------|
| BracketLink | Autolink |

## Notes

- Defined in the same source file as InlineLink and BareLink
  (`link.py`).
