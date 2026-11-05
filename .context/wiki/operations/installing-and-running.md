# Installing and Running

## Overview

How to install tiredize and run it by hand, in a hook or in CI. What
the arguments, output and exit statuses mean is on the
[CLI](../components/cli.md) page; the configuration file formats are on
the component pages it links.

## Installing

Tiredize needs Python 3.10 or later. Install it from a clone:

```bash
git clone https://github.com/tired-labs/tiredize.git
cd tiredize
pip install -e .
```

Releases are published to TestPyPI only (see [releasing](./releasing.md)).

## Running

```bash
tiredize --markdown-schema schema.yaml --frontmatter-schema fm.yaml --rules rules.yaml docs/*.md
python3 -m tiredize [same arguments]
```

Both forms behave identically. In a hook or CI job, prefer
`python3 -m tiredize`, which works when the console script is not on
`PATH`; write `python -m` only where `python` is known to be the
interpreter tiredize was installed into, since many systems ship only
`python3`.

Gate on the exit status: `0` is clean, `1` means findings or a runtime
error, `2` is a usage mistake. A `1` with an `error:` line on stderr
means later files were not checked.

## Design Decisions

- **Module execution is the recommended form for automation,** because
  it depends only on the interpreter, not on where pip put the console
  script.
