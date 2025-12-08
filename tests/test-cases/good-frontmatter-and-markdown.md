---
id: MD-001
description: Valid Markdown document for parser testing.
elements:
- frontmatter
- lists
- markdown
- sections
- tables
tags:
- markdown
- testing
- tiredize
pub_date: 1970-01-01
---

# H1 Title: Markdown Feature Coverage

This document is intentionally written to exercise as many common Markdown
constructs as possible. It is meant to be a valid, boring, highly structured
example. It will be used by a test case stored in a [local file].

This is a paragraph with an inline link to [TIRED
Labs](https://example.com/tired-labs) and another to a [reference style
link][ref-example].

Here is a bare URL that should be detected as an autolink:
https://example.com/autolink-test

Here is the angle bracket form: <https://example.com/angle-link>.

Inline formatting: **bold text**, *italic text*, and `inline code`.

---

## H2 Section: Lists and Images

### Unordered list

- Item one with an inline link to [GitHub](https://github.com).
- Item two with inline code `tiredize run file.md`.
- Item three referencing a definition link [project site][ref-example].

### Ordered list

1. First ordered item.
2. Second ordered item with nested list:
   - Nested bullet one.
   - Nested bullet two with `code`.
3. Third ordered item.

### Images

Inline image:

![TIRED Logo - Inline](https://avatars.githubusercontent.com/u/235505457 "TIRED
Logo")

Reference style image:

![TIRED Logo - Reference style][img-logo]

---

## H2 Section: Blockquotes and Code

### H3 Subsection: Blockquote

> This is a blockquote used to test parsing. It contains a [link inside the
> quote](https://example.com/inside-quote).

### H3 Subsection: Fenced Code Blocks

A typical python code block:

```python
def tiredize(path: str) -> None:
    print(f"Validating {path!r}")

    # Example shell command
    tiredize docs/trr/TRR0001.md
```

A trickier nested codeblock (inception-style):

````markdown
### H3 Subsection: Fenced Code Blocks

A typical python code block:

```python
def tiredize(path: str) -> None:
    print(f"Validating {path!r}")

    # Example shell command
    tiredize docs/trr/TRR0001.md
```
````

## H2 Section: Tables

### H3 Simple Table

| Column A | Column B |
|----------|----------|
| 1        | 2        |
| 3        | 4        |

### H3 Table With Inline Code And Escaped Pipes

| Command              | Description                |
|----------------------|----------------------------|
| `echo "home" \| ls` | List files in the home dir |
| `cd`                 | Change directory           |
| `ls -la`             | List with details          |

### H3 Alignment Variants

| Left Align | Center Align | Right Align |
|:-----------|:------------:|------------:|
| one        |     two      |           3 |
| four       |     five     |           6 |

---

## H2 Section: Headings Up To Level 6

### H3 Heading Level 3

Some text under an H3 heading.

#### H4 Heading Level 4

Some text under an H4 heading.

##### H5 Heading Level 5

Some text under an H5 heading.

###### H6 Heading Level 6

Some text under an H6 heading.

---

## H2 Section: Mixed Content

Paragraph before a list.

- Bullet with a [shortcut to the images section][images].

Another paragraph after the list that ends with an inline code example: `python -m tiredize`.

A horizontal rule follows.

---

[images]: #images
[img-logo]: https://avatars.githubusercontent.com/u/235505457
[local file]: ../test_parser.py
[ref-example]: https://github.com/tired-labs/
