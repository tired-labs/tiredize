# Continuous Integration

## Overview

What GitHub Actions runs for tiredize. The test rules are on
[testing](./testing.md).

## Workflows

`.github/workflows/ci.yaml` runs on pushes to `main`, on every pull
request and by hand. On Python 3.12 it:

1. installs uv (see [Locked dependencies](#locked-dependencies));
2. installs the locked tools and the `coverage` group, then tiredize
   itself, with `uv sync --locked`;
3. runs `flake8 tiredize tests`;
4. runs `pytest --cov=tiredize --cov-report=xml`;
5. uploads coverage to Coveralls with the `coveralls` package from the
   lock, which does not fail the build if the upload fails.

`ci.yaml` does not run on tag pushes and publishes nothing.

`.github/workflows/release.yaml` runs on pushes of `v*` tags and by
hand. It runs flake8 and the full test suite on Python 3.12 and, only
if they pass, builds tiredize and publishes it to TestPyPI and, for a
release tag, to PyPI. Its jobs, guards and use are on
[releasing](../operations/releasing.md).

These two are the only workflows. Dependabot is configured in
`.github/dependabot.yml`.

Neither workflow uses a stored secret. Publishing uses Trusted
Publishing, and the Coveralls upload authenticates with the job's own
`GITHUB_TOKEN`, which works because the repository is public; a
private repository would need a `COVERALLS_REPO_TOKEN` secret. The
`tired-labs` organization makes every workflow's `GITHUB_TOKEN`
read-only unless the workflow asks for more.

Every action either workflow uses is pinned to a full commit SHA, with
the release it was resolved from in a comment, such as
`actions/checkout@<sha>  # v7.0.1`. To update an action, resolve the
new release's tag to its commit (dereferencing an annotated tag) and
replace both the SHA and the comment.

Dependabot (`.github/dependabot.yml`) proposes those updates: once a
week it opens one pull request for all actions with a release at least
14 days old. Before merging one, read the release notes, above all
for a new major version. CI on the pull request runs only `ci.yaml`,
so after merging an update that touches `release.yaml`, run `Release`
by hand on `main` before the next release.

## Locked dependencies

Every Python package either workflow installs comes from `uv.lock`,
which pins an exact version and sha256 hashes for each package,
nested dependencies included. No step installs a package the lock
does not hold, and both workflows install only the groups their job
uses.

**Declaring tools.** Development and release tools are PEP 735
dependency groups in `pyproject.toml`, with minimum versions only.
The groups are the one place a tool is added or its minimum changed.

| Group      | Holds                                              | Installed by |
|------------|----------------------------------------------------|--------------|
| `dev`      | flake8, pytest, pytest-cov, and the `release` group | `uv sync` (the default group); the test jobs of both workflows |
| `release`  | build, hatchling, hatch-vcs, editables             | the `build` job alone (`--only-group release`); `dev` includes it |
| `coverage` | coveralls                                          | the Coveralls upload in `ci.yaml` alone |

`dev` includes `release` because installing tiredize in editable mode
runs the build backend. Runtime dependencies (`PyYAML`, `requests`)
stay in `[project.dependencies]` with minimums, and are locked too.
`[build-system] requires` names no version, so people building from
source are not bound by the CI tools.

**Regenerating the lock.** After changing a group or a dependency
declaration, run `uv lock` and commit `uv.lock`. Never edit the lock by
hand. `uv lock --check` fails when the lock is out of date. The lock
is universal: it covers every Python version tiredize supports (3.10
and later), and CI installs only the Python 3.12 resolution.

**Installing in a workflow.**

- uv is installed by `astral-sh/setup-uv`, pinned to a commit SHA,
  at a fixed uv version. The Action checks the download against its
  own built-in checksum list; the check is never skipped.
- `uv sync --locked`, `uv run --locked` and `uv export --locked` fail
  rather than change the lock. Installs from an exported file use
  `--require-hashes`.
- tiredize is installed in two steps: the locked tools first
  (`--no-install-project`), then tiredize with `--no-build-isolation`.
  Without that flag the build would fetch hatchling and hatch-vcs
  unlocked into an isolated environment. The same flag is on every
  `uv run`, so uv does not rebuild tiredize with fetched tools.

**Cooldown.** `[tool.uv]` in `pyproject.toml` sets `exclude-newer` to
14 days, so `uv lock` resolves only releases at least that old, the
same cooldown Dependabot uses. tiredize itself is exempt, through a
per-package cutoff date far in the future, because the TestPyPI
install check installs the version uploaded seconds earlier (see
[releasing](../operations/releasing.md)).

**Dependabot's `uv` updates.** The `uv` ecosystem has the same weekly
schedule, single group and 14-day cooldown as actions. Its
`versioning-strategy: lockfile-only` makes it change `uv.lock`, versions
and hashes together, and never the minimums in `pyproject.toml`.
Dependabot runs only on `main`, and CI on its pull request runs only
`ci.yaml`; after merging an update, run `Release` by hand as above, so
the release path sees the new tools.

Local setup is on [testing](./testing.md).

## Design Decisions

- **Actions are pinned to commit SHAs, not tags.** A tag can be moved
  to new code; a SHA cannot. This matters most in the publish jobs,
  which hold `id-token: write` and so can publish tiredize.
- **Dependabot updates the pins, with a 14-day cooldown,** so the pins
  do not go stale and a bad or compromised release has time to be
  found before it is proposed.
- **Every installed package is locked, with hashes checked,** nested
  dependencies included, so a tampered or newly broken release cannot
  reach CI or a release by floating. An unpinned hatchling 1.33.0 broke
  the first TestPyPI upload.
- **Tools are dependency groups, not extras,** because groups are not
  published in the package metadata. The lock is generated from them.
- **uv, because Dependabot can update its lock from groups.** Dependabot
  regenerates a compiled lock only from `.in` files, not from dependency
  groups, but updates `uv.lock` directly, so uv keeps the groups as the
  one place to edit. uv is therefore a requirement for working on
  tiredize.
- **Both workflows run Python 3.12,** the newer of the two versions
  that were in use. Jobs that run no Python tooling (`tag-guard`, the
  publish jobs) set up no Python.
- **`coveralls` from the lock, not the Coveralls Action.** The Action
  downloads its reporter program at run time, `latest` by default,
  checked only against a checksum from the same release. The package
  is hash-checked from the lock and updated by Dependabot. It is
  maintained by Kevin James, not by Coveralls.
- **`twine check` is not run.** The publish Action runs it before the
  TestPyPI upload, which comes before PyPI, and twine would add about
  25 packages to the lock.
