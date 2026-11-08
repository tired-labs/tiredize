# Installing and Running

## Overview

How to install tiredize and run it by hand, in a hook or in CI. What
the arguments, output and exit statuses mean is on the
[CLI](../components/cli.md) page; the configuration file formats are on
the component pages it links.

## Installing

Tiredize declares Python 3.10 as its minimum (`requires-python` in
`pyproject.toml`). CI tests on 3.11 and the release workflow on 3.12
(see [CI](../practices/ci.md)).

Releases are published to PyPI by the release workflow (see
[releasing](./releasing.md)). Install the latest release, or a given
one, and check what is installed:

```bash
python3 -m pip install tiredize
python3 -m pip install tiredize==X.Y.Z
tiredize --version
```

PyPI holds only releases; the dev versions of practice runs go to
TestPyPI. A release reaches PyPI only when a `vX.Y.Z` tag is pushed and
its publication approved.

To run the code in a clone, set it up with
[uv](https://docs.astral.sh/uv/). `uv sync` creates a `.venv` and
installs tiredize in editable mode with the development tools at the
versions in `uv.lock` (see [CI](../practices/ci.md)):

```bash
git clone https://github.com/tired-labs/tiredize.git
cd tiredize
uv sync
```

A clone needs its tags for the version to be right (see
[releasing](./releasing.md)); `git clone` fetches them, a shallow clone
may not. The editable install keeps the version it had when it ran,
until `uv sync --reinstall-package tiredize` reinstalls it.

## Running

```bash
tiredize --markdown-schema schema.yaml --frontmatter-schema fm.yaml --rules rules.yaml docs/*.md
python3 -m tiredize [same arguments]
```

Both forms behave identically (see [CLI](../components/cli.md) for
the one difference, in tracebacks). In a hook or CI job, prefer
`python3 -m tiredize`, which works when the console script is not on
`PATH`; write `python -m` only where `python` is known to be the
interpreter tiredize was installed into, since many systems ship only
`python3`.

Gate on the exit status: `0` is clean, `1` means findings or a runtime
error, `2` is a usage mistake. A `1` with an `error:` line or a Python
traceback on stderr means a runtime error stopped the run and later
files were not checked.

## Design Decisions

- **Module execution is the recommended form for automation,** because
  it depends only on the interpreter, not on where pip put the console
  script.
