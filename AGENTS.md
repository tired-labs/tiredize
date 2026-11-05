# AGENTS.md

Read `.context/wiki/README.md` to understand how tiredize works, why,
and how it is changed, and `.context/local/` if it exists. Work not yet
done is in `.context/tracker/`.

## Knowledge Mapping

Knowledge files loaded per workflow step (see the global Knowledge
Mapping convention). Each step's agent receives its base function plus
the files listed here for that step, plus any issue-level `knowledge`.

```yaml
knowledge:
  software-engineering:
    acceptance-test-design:
      - testing
    implementation:
      - git
      - python
      - testing
    code-and-test-review:
      - code-review
      - python
      - testing
    acceptance-verification:
      - testing
    technical-reference:
      - specifications
    architecture-review:
      - specifications
    closeout:
      - git
```
