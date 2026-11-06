# Standard library
from __future__ import annotations
from pathlib import Path
import re
import subprocess

# Third party
import pytest


# Acceptance tests for where tiredize's version comes from
# (issue `pypi-release`, Versioning criteria).
#
# These are static, offline checks of the public build configuration:
# `pyproject.toml` must hand the version to hatch-vcs, which reads it
# from git tags, with `local_scheme = "no-local-version"` so a dev
# version never carries a "+g<hash>" segment that PyPI and TestPyPI
# reject; and no tracked file may hold a version number of its own.
#
# They build nothing, install nothing and touch no network. That a
# tagged build really yields its tag's version, and an untagged one a
# dev version sorting after the last tag, is a one-time check at
# Acceptance Verification, not a test here.
#
# `pyproject.toml` is read with `tomllib`, which is Python 3.11+;
# these tests skip on 3.10.


REPO_ROOT = Path(__file__).resolve().parent.parent

HATCH_VCS = re.compile(r"hatch[-_.]vcs(?![\w.-])", re.IGNORECASE)

VERSION_FILE_NAMES = {"VERSION", "version.py", "_version.py"}

LITERAL_DUNDER_VERSION = re.compile(
    r"^\s*__version__\s*(?::[^=]*)?=\s*[rRbBuU]?['\"]", re.MULTILINE
)


def _pyproject() -> dict:
    tomllib = pytest.importorskip("tomllib")
    with open(REPO_ROOT / "pyproject.toml", "rb") as handle:
        return tomllib.load(handle)


def _hatch_version(pyproject: dict) -> dict:
    return pyproject.get("tool", {}).get("hatch", {}).get("version", {})


def _tracked_files() -> list[str]:
    return subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()


# --- The version comes from git tags through hatch-vcs -----------------


class TestVersionSource:
    def test_build_requires_hatch_vcs(self):
        requires = _pyproject()["build-system"]["requires"]
        assert any(
            HATCH_VCS.match(requirement.strip()) for requirement in requires
        ), requires

    def test_version_source_is_vcs(self):
        assert _hatch_version(_pyproject()).get("source") == "vcs"

    def test_dev_versions_drop_the_local_segment(self):
        raw_options = _hatch_version(_pyproject()).get("raw-options", {})
        assert raw_options.get("local_scheme") == "no-local-version"

    def test_version_is_dynamic(self):
        assert "version" in _pyproject()["project"].get("dynamic", [])


# --- No file in the repository holds a version number -----------------


class TestNoHardcodedVersion:
    def test_no_tracked_file_holds_a_version(self):
        pyproject = _pyproject()
        assert "version" not in pyproject["project"], (
            "pyproject.toml [project] holds a version"
        )
        # A fallback is a version number written in a file too.
        hatch_version = _hatch_version(pyproject)
        assert "fallback-version" not in hatch_version
        assert "fallback_version" not in hatch_version.get(
            "raw-options", {}
        )

        tracked = _tracked_files()
        version_files = [
            path for path in tracked
            if Path(path).name in VERSION_FILE_NAMES
        ]
        assert version_files == []
        offenders = [
            path for path in tracked
            if path.startswith("tiredize/") and path.endswith(".py")
            and LITERAL_DUNDER_VERSION.search(
                (REPO_ROOT / path).read_text(encoding="utf-8")
            )
        ]
        assert offenders == []
