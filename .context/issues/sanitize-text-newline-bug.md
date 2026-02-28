Status: draft
Parent: test-coverage-audit.md

# sanitize_text() Trailing Newline Bug

## Summary

The `sanitize_text()` utility function in `tiredize/markdown/utils.py`
drops trailing newlines from matched regions when replacing them with
whitespace. This is caused by `str.splitlines()` treating a trailing
`\n` as a line terminator rather than creating an empty final element.
The result is a sanitized string that is shorter than the original,
violating the length-preservation contract that all sanitize methods
depend on.

Identified during the test coverage audit
(`test-coverage-markdown-types.md`). 3 skipped spec tests document
the bug.

## Root Cause

In `tiredize/markdown/utils.py` lines 32-36:

```python
old_lines = match.group().splitlines()
new_lines: list[str] = []
for old_line in old_lines:
    new_lines.append(" " * len(old_line))
result += "\n".join(new_lines)
```

When `match.group()` ends with `\n`, `splitlines()` produces N
elements (one per line), but the original text has N-1 `\n` characters
between lines PLUS 1 trailing `\n`. The `"\n".join()` only produces
N-1 `\n` characters, losing the trailing one.

Example: `"---\nfoo\n---\n"` has 4 lines in `splitlines()`:
`['---', 'foo', '---']` -- wait, that's only 3. The trailing `\n`
causes `splitlines()` to treat `---` as a complete line rather than
creating an empty 4th element. So `"\n".join()` produces 2 `\n`
characters instead of 3, making the result 1 character shorter.

## Findings

### Skipped spec tests (3)

1. **FrontMatter.sanitize() preserves length**
   `test_frontmatter.py::test_frontmatter_sanitize_preserves_length`
   `len(sanitized) != len(text)` because the frontmatter match ends
   with `\n` (the closing `---\n`).

2. **FrontMatter.sanitize() idempotent**
   `test_frontmatter.py::test_frontmatter_sanitize_idempotent`
   Second call produces different result because string length
   changed, shifting match positions.

3. **Header not extracted from sanitized frontmatter**
   `test_frontmatter.py::test_header_not_extracted_from_frontmatter`
   After FrontMatter.sanitize(), `# Real Header` is appended to the
   last sanitized line without a preceding newline. The header
   regex's start-of-line anchor fails, causing the header to be
   invisible to downstream extraction.

### Impact beyond length preservation

Finding #3 reveals the bug is more severe than just string length:
it corrupts downstream extraction by removing newlines that other
extractors depend on for start-of-line anchors. Any element type
whose regex match ends with `\n` will cause the next element in the
text to be incorrectly joined to the sanitized region.

### Affected patterns

Patterns whose matches typically end with `\n`:
- FrontMatter (`---\n` closing delimiter includes `\n`)
- Table (rows pattern ends with `(\n|$)`)
- CodeBlock (closing fence line includes content before it)

Patterns whose matches never end with `\n`:
- CodeInline, InlineLink, BracketLink, BareLink, InlineImage,
  Header, QuoteBlock, ReferenceDefinition, LinkReference,
  ImageReference

## Acceptance Criteria

- [ ] `sanitize_text()` preserves string length for all inputs,
      including matches that end with `\n`
- [ ] All 3 skipped spec tests unskipped and passing
- [ ] No regressions in existing tests
- [ ] The fix handles edge cases: match ending with multiple `\n`,
      match that is entirely `\n` characters

## Out of Scope

- Sanitization chain ordering (tracked in
  `parser-sanitization-gaps.md`)
- GFM syntax support (tracked in `gfm-parity.md`)

## Design Decisions

## Open Questions

- Should the fix use `split('\n')` instead of `splitlines()`?
  `"foo\n".split('\n')` gives `['foo', '']` which preserves the
  trailing empty element.
- Does `splitlines()` handle `\r\n` differently from `split('\n')`?
  If CRLF support is added later, the fix should account for both.
