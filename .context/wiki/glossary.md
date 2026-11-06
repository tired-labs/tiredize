# Glossary

- **Autolink**: a URI or email address in angle brackets, GFM section 6.8. See [autolinks](./components/autolinks.md).
- **Dev version**: the version an untagged commit builds, such as `0.1.1.dev3`; it sorts after the last release. See [releasing](./operations/releasing.md).
- **Element**: one typed piece of markdown the parser extracts, such as a table or an inline link. See [markdown parser](./components/markdown-parser.md).
- **Element vocabulary**: the names rules use for element types in `disallow` and `exclude`. See [linter engine](./components/linter-engine.md).
- **Extended autolink**: a bare URL, `www.` address or email address in prose, GFM section 6.9. See [autolinks](./components/autolinks.md).
- **Finding**: what a check reports about a document; it does not stop the run. See [pipeline](./architecture/pipeline.md).
- **Frontmatter**: the YAML block at the very start of a document. See [markdown parser](./components/markdown-parser.md).
- **GFM**: GitHub Flavored Markdown, the specification the parser measures itself against. See [scope](./overview/scope.md).
- **Release tag**: a git tag `vX.Y.Z` on `main`; pushing one starts the release of version `X.Y.Z`. See [releasing](./operations/releasing.md).
- **Rule id**: the name of a linter rule, taken from its module filename. See [linter engine](./components/linter-engine.md).
- **Runtime error**: a problem that stops a check from running, such as a bad configuration file; it stops the run. See [CLI](./components/cli.md).
- **Sanitize**: blank an element's text with spaces, keeping every offset, so later extractors do not match inside it. See [markdown parser](./components/markdown-parser.md).
- **Schema entry**: one section definition in a markdown schema, matched by `name` or `pattern`. See [markdown schema validator](./components/markdown-schema-validator.md).
- **Section**: a heading and the text up to the next heading. See [markdown parser](./components/markdown-parser.md).
- **Slug**: the `#anchor` GitHub gives a heading, used to resolve anchor links. See [markdown parser](./components/markdown-parser.md).
- **Trusted Publishing**: publishing to PyPI and TestPyPI with a short-lived GitHub OIDC token instead of a stored secret. See [releasing](./operations/releasing.md).
- **TRR**: Technique Research Report, the TIRED Labs document type tiredize was built for. See [scope](./overview/scope.md).
