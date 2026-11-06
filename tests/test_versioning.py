# Standard library
from __future__ import annotations
from pathlib import Path
import email.parser
import os
import re
import shutil
import subprocess
import sys
import zipfile

# Third party
from packaging.version import Version
import pytest


# Acceptance tests for how tiredize is versioned and packaged
# (issue `pypi-release`, Versioning criteria).
#
# These are black-box tests. They build the package the way any user
# or the release workflow would, with `pip wheel` and its isolated
# build environment, and read the version from the wheel that comes
# out. They do not import the build backend or its plugins.
#
# Every build happens in a throwaway git repository under tmp_path,
# made from a copy of the working tree (tracked files plus untracked
# files that are not ignored), so the tests see uncommitted changes and
# never create, move or read tags in the real repository. Commits in
# the throwaway repository bypass any configured git hooks.
#
# Network: `pip wheel` fetches the build backend into its isolated
# environment, exactly as `pip install -e .` already does in CI and in
# the documented development setup. No other network access happens.
#
# `pyproject.toml` is read with `tomllib`, which is Python 3.11+;
# those tests skip on 3.10.


REPO_ROOT = Path(__file__).resolve().parent.parent

GIT_IDENTITY = [
    "-c", "core.hooksPath=/dev/null",
    "-c", "commit.gpgSign=false",
    "-c", "tag.gpgSign=false",
    "-c", "user.name=Sleepy Tester",
    "-c", "user.email=sleepy@example.invalid",
]


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *GIT_IDENTITY, *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _copy_working_tree(destination: Path) -> Path:
    """Copy the working tree, minus ignored files, into `destination`."""
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others",
         "--exclude-standard"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8")
    for relative in filter(None, listing.split("\0")):
        source = REPO_ROOT / relative
        if not source.is_file():
            continue  # deleted in the working tree but not yet staged
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return destination


def _scratch_repo(directory: Path) -> Path:
    """A fresh git repository holding a copy of the working tree."""
    repo = _copy_working_tree(directory / "tiredize-copy")
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Initial nap")
    return repo


def _commit_snooze(repo: Path, note: str) -> None:
    """Add one more commit that changes nothing that matters."""
    (repo / "snooze.txt").write_text(note, encoding="utf-8")
    _git(repo, "add", "snooze.txt")
    _git(repo, "commit", "-q", "-m", note)


def _build_wheel(repo: Path, out: Path) -> Path:
    """Build a wheel of `repo` with pip and return its path."""
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", "--no-deps",
         "--disable-pip-version-check", "-q", "-w", str(out), str(repo)],
        capture_output=True,
        text=True,
        check=True,
    )
    wheels = list(out.glob("tiredize-*.whl"))
    assert len(wheels) == 1, f"expected one tiredize wheel, got {wheels}"
    return wheels[0]


def _wheel_metadata(wheel: Path):
    """The parsed METADATA file of a wheel."""
    with zipfile.ZipFile(wheel) as archive:
        name = next(
            entry for entry in archive.namelist()
            if re.fullmatch(r"[^/]+\.dist-info/METADATA", entry)
        )
        text = archive.read(name).decode("utf-8")
    return email.parser.Parser().parsestr(text)


def _wheel_version(wheel: Path) -> str:
    return _wheel_metadata(wheel)["Version"]


def _pyproject() -> dict:
    tomllib = pytest.importorskip("tomllib")
    with open(REPO_ROOT / "pyproject.toml", "rb") as handle:
        return tomllib.load(handle)


@pytest.fixture(scope="module")
def tagged_wheel(tmp_path_factory) -> Path:
    """A wheel built from a commit carrying the annotated tag v4.2.0."""
    base = tmp_path_factory.mktemp("tagged")
    repo = _scratch_repo(base)
    _git(repo, "tag", "-a", "v4.2.0", "-m", "The answer, released")
    return _build_wheel(repo, base / "dist")


# --- The version lives only in git tags -------------------------------


class TestNoVersionInRepository:

    def test_version_source_is_hatch_vcs(self):
        pyproject = _pyproject()
        requires = pyproject["build-system"]["requires"]
        assert any(
            re.match(r"hatch-vcs\b", requirement.replace("_", "-"))
            for requirement in requires
        ), requires
        version = pyproject.get("tool", {}).get("hatch", {}).get(
            "version", {}
        )
        assert version.get("source") == "vcs"

    def test_no_tracked_file_holds_a_version(self):
        project = _pyproject()["project"]
        assert "version" not in project, "pyproject.toml holds a version"
        assert "version" in project.get("dynamic", [])
        tracked = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        version_files = [
            path for path in tracked
            if Path(path).name in {"VERSION", "version.py", "_version.py"}
        ]
        assert version_files == []
        literal_dunder = re.compile(
            r"^\s*__version__\s*=\s*['\"]", re.MULTILINE
        )
        offenders = [
            path for path in tracked
            if path.startswith("tiredize/") and path.endswith(".py")
            and literal_dunder.search(
                (REPO_ROOT / path).read_text(encoding="utf-8")
            )
        ]
        assert offenders == []


# --- A tagged commit builds exactly its tag's version -----------------


class TestTaggedBuild:
    def test_annotated_tag_gives_its_version(self, tagged_wheel):
        assert _wheel_version(tagged_wheel) == "4.2.0"

    def test_lightweight_tag_gives_its_version(self, tmp_path):
        repo = _scratch_repo(tmp_path)
        _git(repo, "tag", "v4.2.0")
        wheel = _build_wheel(repo, tmp_path / "dist")
        assert _wheel_version(wheel) == "4.2.0"

    def test_wheel_filename_carries_the_version(self, tagged_wheel):
        assert tagged_wheel.name.startswith("tiredize-4.2.0-")


# --- Any other commit builds a dev version after the last tag ---------


class TestUntaggedBuild:
    def test_commit_after_tags_sorts_after_the_last_tag(self, tmp_path):
        repo = _scratch_repo(tmp_path)
        _git(repo, "tag", "v0.1.0")
        _commit_snooze(repo, "five more minutes")
        _git(repo, "tag", "v0.2.0")
        _commit_snooze(repo, "ten more minutes")
        version = Version(_wheel_version(
            _build_wheel(repo, tmp_path / "dist")
        ))
        assert version.is_devrelease, str(version)
        assert version > Version("0.2.0"), str(version)
        # local_scheme = "no-local-version": no "+g<hash>" segment,
        # which PyPI and TestPyPI would reject.
        assert version.local is None, str(version)

    def test_dirty_tree_has_no_local_segment(self, tmp_path):
        repo = _scratch_repo(tmp_path)
        _git(repo, "tag", "v0.2.0")
        _commit_snooze(repo, "hit snooze")
        (repo / "snooze.txt").write_text("uncommitted yawn", "utf-8")
        version = Version(_wheel_version(
            _build_wheel(repo, tmp_path / "dist")
        ))
        assert version.is_devrelease, str(version)
        assert version > Version("0.2.0"), str(version)
        assert version.local is None, str(version)


# --- The installed version is what --version reports ------------------


class TestInstalledVersion:
    def test_installed_wheel_reports_its_tag(self, tagged_wheel, tmp_path):
        # Install the tagged wheel alone into a directory placed first
        # on sys.path, so both `import tiredize` and its distribution
        # metadata resolve to this wheel, not the development install.
        # cwd is tmp_path so the repository is not on sys.path.
        target = tmp_path / "site"
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--no-deps",
             "--disable-pip-version-check", "-q", "--target",
             str(target), str(tagged_wheel)],
            capture_output=True,
            text=True,
            check=True,
        )
        env = dict(os.environ, PYTHONPATH=str(target))
        result = subprocess.run(
            [sys.executable, "-m", "tiredize", "--version"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        assert "4.2.0" in result.stdout.split()


# --- Package metadata -------------------------------------------------


class TestAuthor:
    def test_pyproject_author_is_tired_labs_without_email(self):
        assert _pyproject()["project"]["authors"] == [
            {"name": "TIRED Labs"}
        ]

    def test_wheel_metadata_author_is_tired_labs(self, tagged_wheel):
        metadata = _wheel_metadata(tagged_wheel)
        assert metadata["Author"] == "TIRED Labs"
        assert metadata["Author-email"] is None
