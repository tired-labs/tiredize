# Parser Robustness: Regex Backtracking and Sanitization Gaps

## Summary

Testing tiredize against real-world TRR documents exposed two parser
bugs that combined to cause the tool to hang indefinitely on certain
files. Both have been fixed, but the investigation revealed broader
concerns about regex safety and sanitization consistency across all
markdown type extractors.

## Bugs Fixed

### 1. Catastrophic Regex Backtracking in Table Divider

**File:** `tiredize/markdown/types/table.py`

**Root cause:** The `RE_TABLE` divider pattern used
`([ \t]*:?-+:?[ \t]*[|]?)*[|]` — an optional pipe `[|]?` inside a
repeating group followed by a mandatory pipe `[|]`. When the regex
encountered a long sequence of dashes without any pipes (e.g.,
` -----------------` from formatted output inside a code block), the
engine tried every possible way to partition the dashes across group
iterations — exponential O(2^n) time.

**Fix:** Rewrote the divider as two alternatives, each with mandatory
pipes inside the repeating group:

```
[|][ \t]*:?-+:?[ \t]*([|][ \t]*:?-+:?[ \t]*)*[|]?\n
|
[ \t]*:?-+:?[ \t]*([|][ \t]*:?-+:?[ \t]*)+[|]?\n
```

First alternative handles leading-pipe tables (`|---|---|`), second
handles no-leading-pipe tables (`---|---`). Mandatory `[|]` inside each
group eliminates backtracking because dashes cannot satisfy `[|]`.

**Tests:** 3 new tests in `tests/markdown/types/test_table.py`:
`test_long_dashes_no_backtracking`, `test_dashes_inside_code_block_text`,
`test_aligned_divider`.

### 2. Table Extraction on Unsanitized Code Block Content

**File:** `tiredize/markdown/types/section.py`

**Root cause:** `Table.extract()` in `Section._extract()` received raw
`string` instead of code-block-sanitized text. This caused the table
regex to run against content inside fenced code blocks, producing both
false table matches and triggering the backtracking bug above.

**Fix:** Changed `Table.extract(text=string, ...)` to
`Table.extract(text=CodeBlock.sanitize(string), ...)`.

**Test:** 1 new test in `tests/markdown/types/test_section.py`:
`test_table_inside_code_block_not_extracted`.

## Broader Concerns

### Regex Safety Audit Needed

The table regex was the only confirmed catastrophic backtracking case,
but other patterns in `markdown/types/` have not been stress-tested
against adversarial input. Patterns of concern:

- `RE_URL` in `link.py` uses `\S+` which could be slow on very long
  non-whitespace strings, though it's not obviously exponential.
- Any pattern using `.*` or `.+` followed by a literal could
  potentially backtrack on long non-matching input.

**Recommendation:** Write targeted stress tests for every `RE_*`
constant in the codebase, feeding each one strings of increasing length
(e.g., 100, 1000, 10000 characters) with content designed to maximize
backtracking. Any test that exceeds a time threshold indicates a
vulnerable pattern.

### Sanitization Consistency Audit Needed

The sanitize chain in `Section._extract()` is inconsistent. Some
extractors receive raw `string`, others use `string_safe` (which has
code blocks and inline code sanitized out). The current state:

| Extractor | Input | Sanitized? |
|-----------|-------|------------|
| `CodeBlock.extract()` | `string` | N/A (highest precedence) |
| `CodeInline.extract()` | `string` | No |
| `InlineImage.extract()` | `string` | No |
| `ImageReference.extract()` | `string` | No |
| `BareLink.extract()` | `string` | No (does internal sanitization) |
| `BracketLink.extract()` | `string` | No (does internal sanitization) |
| `InlineLink.extract()` | `string` | No (does internal sanitization) |
| `LinkReference.extract()` | `string` | No (does internal sanitization) |
| `List.extract()` | `string` | No |
| `QuoteBlock.extract()` | `string` | No |
| `ReferenceDefinition.extract()` | `string` | No |
| `Table.extract()` | `CodeBlock.sanitize(string)` | **Yes (fixed)** |

Link extractors do their own internal sanitization, which is better
than nothing but means each extractor independently decides what to
sanitize — there's no single source of truth for the sanitize chain.

**Recommendation:** Evaluate whether all extractors that can produce
false positives inside code blocks should receive pre-sanitized input.
This is particularly relevant for `InlineImage`, `ImageReference`,
`List`, and `QuoteBlock` — all of which could match syntax inside
code fences.

## Trigger Document

The bug was discovered when running tiredize against TRR0016 in the
techniques repository. Lines 81-93 of
`/home/user/techniques/reports/trr0016/win/README.md` contain a
`text` code block with formatted PowerShell output including long
dash separator lines (`-----------------`). The table divider regex
ran against these dashes and hung.

## References

- Table regex: `tiredize/markdown/types/table.py:19-35`
- Section extraction: `tiredize/markdown/types/section.py:81-158`
- Sanitize helpers: `tiredize/markdown/utils.py`
