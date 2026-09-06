"""Entry point for `python -m tiredize`.

The console script generated from `[project.scripts]` wraps
`tiredize.cli:main` in `sys.exit(...)`; module execution has no such
wrapper, so the exit status has to be raised here. Without it every
`-m` invocation exits `0` and the tool cannot gate CI or a pre-commit
hook.
"""
# Standard library
from __future__ import annotations

# Local
from tiredize.cli import main


# `raise SystemExit(...)` matches the idiom at the bottom of
# `tiredize/cli.py`. A usage error raised by argparse inside `main()`
# is itself a SystemExit and unwinds through this statement untouched.
raise SystemExit(main())
