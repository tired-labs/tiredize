# AGENTS.md

Read and follow all instruction files in the `.context/` directory of this
repository. Each file provides a different layer of context:

- `.context/PROJECT.md` -- Project-level overview, architecture map, and
  design boundaries for this repository.
- `.context/PYTHON.md` -- Python language conventions and tooling. Reusable
  across Python projects.
- `.context/specifications/` -- Living technical reference for each
  subsystem. How the code works, contracts, patterns, file layout, and
  design decisions.
- `.context/issues/` -- Working issue documents for features in progress.
  Read any issue files relevant to the current task.

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
