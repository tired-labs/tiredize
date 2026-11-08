# Standard library
from __future__ import annotations
import ast
from pathlib import Path
import re
import subprocess
import sys

# Third party
import pytest
import yaml


# Acceptance tests for how tiredize's development and release tools are
# declared, locked, installed and updated (issue `tooling-migration`).
#
# Everything here is a static, offline read of tracked files:
# `pyproject.toml`, `uv.lock`, the two workflows, `dependabot.yml` and
# the test files themselves. Nothing runs uv, pip or a workflow, and
# nothing touches the network. That CI and a manual Release run really
# pass, that uv's checksum check really ran, and that the wiki pages say
# the right things are one-time checks at Acceptance Verification.
#
# The workflow tests read the shell in each `run:` step and judge it
# against the contract (every install comes from `uv.lock`, hashes
# checked, and only the groups the job uses), not against one particular
# way of writing it. `uv sync`, `uv export` piped into `uv pip install`,
# and `pip install -r` of an exported file all satisfy it.
#
# `pyproject.toml` and `uv.lock` are read with `tomllib`, which is
# Python 3.11+; those tests skip on 3.10.


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = {
    "ci.yaml": REPO_ROOT / ".github" / "workflows" / "ci.yaml",
    "release.yaml": REPO_ROOT / ".github" / "workflows" / "release.yaml",
}
SHA_PIN = re.compile(r"^[^@\s]+@[0-9a-f]{40}$")

# The tools the contract names, by the group the issue puts them in.
DEV_TOOLS = ["flake8", "pytest", "pytest-cov"]
RELEASE_TOOLS = ["build", "hatch-vcs", "hatchling"]
RUNTIME_DEPENDENCIES = ["pyyaml", "requests"]


def _norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    assert match, requirement
    return _norm(match.group(1))


def _toml(path: Path) -> dict:
    tomllib = pytest.importorskip("tomllib")
    assert path.is_file(), f"{path.name} does not exist"
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def _pyproject() -> dict:
    return _toml(REPO_ROOT / "pyproject.toml")


def _tracked(path: str) -> bool:
    out = subprocess.run(
        ["git", "ls-files", "--", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return bool(out.strip())


def _groups() -> dict[str, list]:
    groups = _pyproject().get("dependency-groups")
    assert groups, "pyproject.toml has no [dependency-groups] table"
    return groups


def _group_packages(name: str, seen: frozenset = frozenset()) -> set[str]:
    """Normalized package names in a group, include-group expanded."""
    packages: set[str] = set()
    for entry in _groups()[name]:
        if isinstance(entry, str):
            packages.add(_requirement_name(entry))
        elif "include-group" in entry and name not in seen:
            packages |= _group_packages(
                entry["include-group"], seen | {name}
            )
    return packages


def _groups_with(package: str) -> set[str]:
    return {g for g in _groups() if package in _group_packages(g)}


def _workflow(name: str) -> dict:
    path = WORKFLOWS[name]
    assert path.is_file(), f"{path} does not exist"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# --- Shell reading ------------------------------------------------------


def _segments(script: str) -> list[list[str]]:
    """Split a shell script into commands, each a list of words.

    A small reader, not a shell: it honours quotes, `#` comments, line
    continuations, and splits on newlines, `;`, `&`, `|` and
    parentheses outside quotes. That is enough to find the commands a
    step runs.
    """
    script = script.replace("\\\n", " ")
    segments: list[list[str]] = []
    words: list[str] = []
    word: list[str] = []
    in_word = False
    quote = ""
    i = 0

    def end_word() -> None:
        nonlocal in_word
        if in_word:
            words.append("".join(word))
            word.clear()
            in_word = False

    def end_segment() -> None:
        end_word()
        if words:
            segments.append(list(words))
            words.clear()

    while i < len(script):
        c = script[i]
        if quote:
            if c == quote:
                quote = ""
            else:
                word.append(c)
        elif c in "'\"":
            quote = c
            in_word = True
        elif c == "#" and not in_word:
            while i < len(script) and script[i] != "\n":
                i += 1
            continue
        elif c in "\n;&|()":
            end_segment()
        elif c in " \t\r":
            end_word()
        else:
            word.append(c)
            in_word = True
        i += 1
    end_segment()
    return segments


KEYWORDS = {"if", "then", "else", "elif", "do", "while", "until", "!", "{"}


def _commands(segments: list[list[str]]) -> list[list[str]]:
    """Drop leading shell keywords and NAME=value assignments."""
    commands = []
    for words in segments:
        words = list(words)
        while words and (
            words[0] in KEYWORDS or re.match(r"^\w+=", words[0])
        ):
            words.pop(0)
        if words:
            commands.append(words)
    return commands


def _base(word: str) -> str:
    return word.rsplit("/", 1)[-1]


def _classify(words: list[str]) -> tuple[str, list[str]]:
    """Return (kind, arguments after the subcommand)."""
    head = _base(words[0])
    rest = words[1:]
    if head in ("pip", "pip3") and rest[:1] == ["install"]:
        return "pip install", rest[1:]
    if head.startswith("python") and rest[:3] == ["-m", "pip", "install"]:
        return "pip install", rest[3:]
    if head in ("uv", "uvx", "pipx"):
        if head != "uv":
            return head, rest
        if rest[:2] == ["pip", "install"]:
            return "pip install", rest[2:]
        if rest[:2] == ["pip", "sync"]:
            return "pip install", rest[2:]
        if rest[:2] == ["pip", "compile"]:
            return "uv pip compile", rest[2:]
        if rest and rest[0] in ("sync", "run", "export", "lock", "build",
                                "tool", "add", "remove", "venv", "python"):
            return "uv " + rest[0], rest[1:]
        return "uv other", rest
    if head.startswith("python") and rest[:2] == ["-m", "build"]:
        return "build", rest[2:]
    if head.startswith("python") and rest[:2] == ["-m", "uv"]:
        return "uv other", rest[2:]
    if head == "pyproject-build":
        return "build", rest
    return "other", rest


def _flags(args: list[str]) -> set[str]:
    return {a.split("=", 1)[0] for a in args if a.startswith("-")}


def _flag_values(args: list[str], *names: str) -> list[str]:
    values = []
    for i, arg in enumerate(args):
        key, eq, value = arg.partition("=")
        if key in names:
            if eq:
                values.append(value)
            elif i + 1 < len(args):
                values.append(args[i + 1])
    return values


VALUE_OPTIONS = {
    "-r", "--requirement", "-c", "--constraint", "-e", "--editable",
    "-i", "--index-url", "--extra-index-url", "--python", "-p",
    "--target", "--prefix", "-f", "--find-links", "--index",
    "--default-index", "--group", "--only-group", "--no-group",
    "--no-install-package", "--no-build-isolation-package",
    "--output-file", "-o", "--project", "--directory", "--python-version",
    "--platform", "--index-strategy", "--cache-dir", "--config-file",
}


def _positionals(args: list[str]) -> list[str]:
    out = []
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg in VALUE_OPTIONS:
            skip = True
        elif arg.startswith("-"):
            continue
        else:
            out.append(arg)
    out.extend(_flag_values(args, "-e", "--editable"))
    return out


NO_ISOLATION = {"--no-isolation", "-n", "--no-build-isolation"}


def _unisolated(args: list[str]) -> bool:
    flags = _flags(args)
    return bool(flags & NO_ISOLATION) or any(
        f.startswith("--no-build-isolation") for f in flags
    )


def _env_blocks(workflow: dict, job: dict, step: dict) -> str:
    return " ".join(
        str(block.get("env", {}))
        for block in (workflow, job, step)
        if isinstance(block, dict)
    )


def _install_problems(
    workflow: dict, job: dict, step: dict, words: list[str]
) -> list[str]:
    """Everything wrong with one command, judged against the contract."""
    kind, args = _classify(words)
    flags = _flags(args)
    text = " ".join(words)
    problems: list[str] = []

    if re.search(r"astral\.sh|install\.sh", text) and _base(words[0]) in (
        "curl", "wget"
    ):
        problems.append("installs uv by download, not setup-uv")

    if kind in ("uvx", "pipx", "uv tool", "uv add", "uv remove",
                "uv pip compile", "uv other"):
        problems.append(f"`{kind}` installs or resolves outside uv.lock")

    if kind == "uv lock" and not flags & {"--check", "--locked"}:
        problems.append("`uv lock` re-resolves instead of checking")

    if flags & {"--no-verify-hashes", "--no-hashes", "--upgrade", "-U",
                "--upgrade-package", "-P", "--no-require-hashes"}:
        problems.append("skips hash checking or upgrades past the lock")

    if kind in ("uv sync", "uv run", "uv export"):
        if not flags & {"--locked", "--frozen"}:
            problems.append(f"`{kind}` without --locked or --frozen")
    if kind == "uv run" and flags & {"--with", "--with-requirements"}:
        problems.append("`uv run --with` installs outside uv.lock")
    if kind in ("uv sync", "uv run"):
        project_skipped = (
            flags & {"--no-install-project", "--only-group", "--only-dev"}
            or "tiredize" in _flag_values(args, "--no-install-package")
        )
        if not project_skipped and not _unisolated(args):
            problems.append(
                f"`{kind}` builds tiredize in an isolated environment "
                "that fetches unlocked build tools"
            )

    if kind == "pip install":
        requirement_files = _flag_values(args, "-r", "--requirement")
        if requirement_files and "--require-hashes" not in flags:
            problems.append("installs a requirements file without "
                            "--require-hashes")
        for spec in _positionals(args):
            is_wheel_or_sdist = bool(
                re.search(r"\.(whl|tar\.gz|zip)$", spec)
            )
            is_path = spec == "." or "/" in spec or is_wheel_or_sdist
            is_tiredize = _requirement_name(spec) == "tiredize" if \
                re.match(r"[A-Za-z]", spec) else False
            if not (is_path or is_tiredize):
                problems.append(f"installs `{spec}` by name, not from "
                                "uv.lock")
                continue
            if "--no-deps" not in flags:
                problems.append(f"installs `{spec}` with its own "
                                "dependencies, not those in uv.lock")
            if not is_wheel_or_sdist and not is_tiredize and \
                    not _unisolated(args):
                problems.append(f"installs `{spec}` with an isolated "
                                "build that fetches unlocked build tools")

    if kind in ("build", "uv build"):
        constrained = re.search(
            r"UV_BUILD_CONSTRAINT|PIP_CONSTRAINT",
            _env_blocks(workflow, job, step) + text,
        )
        if not _unisolated(args) and not constrained:
            problems.append("builds in an isolated environment that "
                            "fetches unlocked build tools")
    return problems


def _jobs(name: str):
    workflow = _workflow(name)
    for job_id, job in workflow["jobs"].items():
        yield workflow, job_id, job


def _run_commands(job: dict):
    for step in job.get("steps", []):
        if "run" in step:
            for words in _commands(_segments(step["run"])):
                yield step, words


def _effective_groups(job: dict) -> set[str]:
    """Groups the job's uv commands install, by uv's own rules."""
    all_groups = set(_groups())
    uv_config = _pyproject().get("tool", {}).get("uv", {})
    defaults = set(uv_config.get("default-groups", ["dev"]))
    selected: set[str] = set()
    for _step, words in _run_commands(job):
        kind, args = _classify(words)
        if kind not in ("uv sync", "uv run", "uv export"):
            continue
        flags = _flags(args)
        only = _flag_values(args, "--only-group")
        if only or "--only-dev" in flags:
            chosen = {_norm(g) for g in only} | (
                {"dev"} if "--only-dev" in flags else set()
            )
        elif "--all-groups" in flags:
            chosen = set(all_groups)
        else:
            chosen = set() if flags & {"--no-default-groups", "--no-dev"} \
                else set(defaults)
            chosen |= {g for g in all_groups if g in
                       {_norm(x) for x in _flag_values(args, "--group")}}
            if "--dev" in flags:
                chosen.add("dev")
            chosen -= {_norm(x) for x in _flag_values(args, "--no-group")}
        selected |= chosen
    return selected & {_norm(g) for g in all_groups}


TOOL_COMMANDS = {
    "flake8": "flake8",
    "pytest": "pytest",
    "pytest-cov": "pytest",
    "coveralls": "coveralls",
}


def _tools_invoked(job: dict) -> set[str]:
    """Package names whose command the job runs."""
    invoked: set[str] = set()
    for _step, words in _run_commands(job):
        kind, _args = _classify(words)
        if kind in ("build", "uv build"):
            invoked |= {"build", "hatchling", "hatch-vcs"}
        if kind == "pip install" or kind.startswith("uv ") and \
                kind != "uv run":
            continue
        for word in words[:6]:
            for package, command in TOOL_COMMANDS.items():
                if _base(word) == command:
                    invoked.add(package)
    return invoked


def _group_used(group: str, invoked: set[str]) -> bool:
    return bool(_group_packages(group) & invoked)


# --- Dependency groups in pyproject.toml --------------------------------


MINIMUM_ONLY = re.compile(
    r"^\s*[A-Za-z0-9][A-Za-z0-9._-]*(\[[\w,\s-]+\])?\s*>=\s*[0-9][\w.!+*]*"
    r"\s*$"
)


class TestDependencyGroups:
    def test_dev_group_holds_the_test_and_lint_tools(self):
        assert set(DEV_TOOLS) <= _group_packages("dev")

    def test_release_group_holds_the_build_tools(self):
        assert set(RELEASE_TOOLS) <= _group_packages("release")

    def test_every_group_requirement_is_a_minimum_version_only(self):
        offenders = [
            entry
            for entries in _groups().values()
            for entry in entries
            if isinstance(entry, str) and not MINIMUM_ONLY.match(entry)
        ]
        assert not offenders, offenders

    def test_no_group_declares_twine(self):
        assert not _groups_with("twine")


class TestRuntimeAndBuildSystemDeclarations:
    # These hold today; they guard against a lock migration pinning
    # what must stay loose for people installing tiredize.

    def test_runtime_dependencies_keep_minimum_versions(self):
        dependencies = _pyproject()["project"]["dependencies"]
        by_name = {_requirement_name(d): d for d in dependencies}
        assert set(RUNTIME_DEPENDENCIES) <= set(by_name)
        for name in RUNTIME_DEPENDENCIES:
            assert MINIMUM_ONLY.match(by_name[name]), by_name[name]

    def test_build_system_requires_names_no_exact_version(self):
        requires = _pyproject()["build-system"]["requires"]
        assert requires
        assert not [r for r in requires if "==" in r], requires


# --- uv.lock ------------------------------------------------------------


def _lock() -> dict:
    assert _tracked("uv.lock"), "uv.lock is not committed"
    return _toml(REPO_ROOT / "uv.lock")


def _lock_packages() -> dict[str, dict]:
    return {_norm(p["name"]): p for p in _lock().get("package", [])}


def _is_root(package: dict) -> bool:
    source = package.get("source", {})
    return bool({"virtual", "editable", "directory"} & set(source))


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class TestLockFile:
    def test_lock_pins_every_declared_tool_and_runtime_dependency(self):
        packages = _lock_packages()
        declared = set(RUNTIME_DEPENDENCIES)
        for group in _groups():
            declared |= _group_packages(group)
        missing = sorted(declared - set(packages))
        assert not missing, missing

    def test_lock_includes_coveralls(self):
        assert "coveralls" in _lock_packages()

    def test_every_locked_package_has_an_exact_version(self):
        offenders = [
            name for name, package in _lock_packages().items()
            if not _is_root(package)
            and not re.match(r"^\d[\w.!+]*$", str(package.get("version")))
        ]
        assert not offenders, offenders

    def test_every_locked_file_has_a_sha256_hash(self):
        offenders = []
        for name, package in _lock_packages().items():
            if _is_root(package):
                continue
            files = list(package.get("wheels", []))
            if "sdist" in package:
                files.append(package["sdist"])
            if not files:
                offenders.append(f"{name}: no downloadable files")
            offenders += [
                f"{name}: {f.get('url', f)}" for f in files
                if not SHA256.match(str(f.get("hash")))
            ]
        assert not _lock_packages() or not offenders, offenders[:10]
        assert _lock_packages(), "uv.lock holds no packages"

    def test_nested_dependencies_are_locked_too(self):
        packages = _lock_packages()
        assert packages, "uv.lock holds no packages"
        missing = sorted({
            _norm(dep["name"])
            for package in packages.values()
            for dep in package.get("dependencies", [])
        } - set(packages))
        assert not missing, missing
        # A tool with dependencies of its own must bring them along.
        assert len(packages) > len(DEV_TOOLS + RELEASE_TOOLS +
                                   RUNTIME_DEPENDENCIES) + 1


# --- The workflows ------------------------------------------------------


@pytest.mark.parametrize("name", sorted(WORKFLOWS))
class TestWorkflowInstalls:
    def test_every_install_is_from_the_lock_with_hashes_checked(self, name):
        problems = []
        for workflow, job_id, job in _jobs(name):
            for step in job.get("steps", []):
                if "run" not in step:
                    continue
                for words in _commands(_segments(step["run"])):
                    for problem in _install_problems(
                        workflow, job, step, words
                    ):
                        problems.append(f"{job_id}: {problem}: "
                                        f"{' '.join(words)[:80]}")
        assert not problems, problems

    def test_every_job_that_needs_a_group_installs_it_and_no_other(
        self, name
    ):
        problems = []
        for _workflow_, job_id, job in _jobs(name):
            effective = _effective_groups(job)
            invoked = _tools_invoked(job)
            for group in effective:
                if not _group_used(group, invoked):
                    problems.append(
                        f"{job_id} installs group `{group}` it does not "
                        "use"
                    )
            for package in invoked:
                if not any(package in _group_packages(g)
                           for g in effective):
                    problems.append(
                        f"{job_id} runs `{package}` but installs no "
                        "group holding it"
                    )
        assert not problems, problems

    def test_every_python_setup_is_python_3_12(self, name):
        versions = []
        for _w, job_id, job in _jobs(name):
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                if uses.startswith(("actions/setup-python@",
                                    "astral-sh/setup-uv@")):
                    value = step.get("with", {}).get("python-version")
                    if value is not None:
                        versions.append((job_id, str(value)))
        bad = [v for v in versions if not re.match(r"^3\.12(\.\d+)?$", v[1])]
        assert not bad, bad

    def test_every_job_that_runs_python_tooling_sets_up_python_3_12(
        self, name
    ):
        problems = []
        for _w, job_id, job in _jobs(name):
            uses_python = any(
                _base(words[0]).startswith(
                    ("python", "pip", "uv", "pytest", "flake8",
                     "coveralls", "pyproject-build"))
                for _s, words in _run_commands(job)
            )
            if not uses_python:
                continue
            setups = [
                s for s in job.get("steps", [])
                if str(s.get("uses", "")).startswith(
                    ("actions/setup-python@", "astral-sh/setup-uv@"))
                and re.match(r"^3\.12(\.\d+)?$",
                             str(s.get("with", {}).get("python-version")))
            ]
            if not setups:
                problems.append(job_id)
        assert not problems, problems

    def test_uv_is_installed_by_a_pinned_setup_uv_at_a_fixed_version(
        self, name
    ):
        problems = []
        if not any(
            str(s.get("uses", "")).startswith("astral-sh/setup-uv@")
            for _w, _j, job in _jobs(name)
            for s in job.get("steps", [])
        ):
            problems.append(f"{name} never installs uv with setup-uv")
        for _w, job_id, job in _jobs(name):
            uv_used = any(
                _base(words[0]) in ("uv", "uvx")
                for _s, words in _run_commands(job)
            )
            setups = [
                s for s in job.get("steps", [])
                if str(s.get("uses", "")).startswith("astral-sh/setup-uv@")
            ]
            if uv_used and not setups:
                problems.append(f"{job_id}: uses uv with no setup-uv")
            for step in setups:
                if not SHA_PIN.match(step["uses"].split()[0]):
                    problems.append(f"{job_id}: setup-uv not SHA-pinned")
                options = step.get("with", {})
                version = str(options.get("version", ""))
                if not re.match(r"^\d+\.\d+\.\d+$", version):
                    problems.append(
                        f"{job_id}: uv version `{version}` is not fixed"
                    )
                if "manifest-file" in options:
                    problems.append(f"{job_id}: custom checksum manifest")
                if "checksum" in options and not re.match(
                    r"^[0-9a-f]{64}$", str(options["checksum"]).lower()
                ):
                    problems.append(f"{job_id}: malformed checksum")
        assert not problems, problems

    def test_no_job_runs_twine(self, name):
        offenders = [
            job_id for _w, job_id, job in _jobs(name)
            for _s, words in _run_commands(job)
            if any("twine" in w.lower() for w in words)
        ]
        assert not offenders, offenders

    def test_coveralls_action_is_not_used(self, name):
        offenders = [
            step["uses"] for _w, _j, job in _jobs(name)
            for step in job.get("steps", [])
            if "coverallsapp/github-action" in str(step.get("uses", ""))
        ]
        assert not offenders, offenders


class TestCoverageUpload:
    def test_ci_uploads_coverage_with_the_locked_coveralls_package(self):
        runs_coveralls = [
            job_id for _w, job_id, job in _jobs("ci.yaml")
            if "coveralls" in _tools_invoked(job)
        ]
        assert runs_coveralls, "ci.yaml never runs `coveralls`"
        assert "coveralls" in _lock_packages()

    def test_coveralls_lives_in_a_group_only_the_ci_job_installs(self):
        holders = _groups_with("coveralls")
        assert holders, "coveralls is in no dependency group"
        for tool in DEV_TOOLS + RELEASE_TOOLS:
            assert not (holders & _groups_with(tool)), (holders, tool)
        installers = [
            (name, job_id)
            for name in WORKFLOWS
            for _w, job_id, job in _jobs(name)
            if _effective_groups(job) & holders
        ]
        assert len(installers) == 1, installers
        assert installers[0][0] == "ci.yaml"


# --- Dependabot ---------------------------------------------------------


def _dependabot() -> dict[str, dict]:
    path = REPO_ROOT / ".github" / "dependabot.yml"
    assert path.is_file()
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {u["package-ecosystem"]: u for u in config["updates"]}


class TestDependabot:
    def test_uv_ecosystem_is_configured_for_the_repository_root(self):
        updates = _dependabot()
        assert "uv" in updates, sorted(updates)
        assert updates["uv"]["directory"] == "/"

    def test_uv_updates_share_the_actions_schedule_group_and_cooldown(self):
        updates = _dependabot()
        assert "uv" in updates, sorted(updates)
        uv, actions = updates["uv"], updates["github-actions"]
        assert uv["schedule"]["interval"] == "weekly"
        assert uv["schedule"] == actions["schedule"]
        assert uv["cooldown"]["default-days"] == 14
        assert uv["cooldown"] == actions["cooldown"]
        assert len(uv["groups"]) == 1
        assert list(uv["groups"].values()) == list(actions["groups"].values())

    def test_uv_updates_change_the_lock_and_never_the_minimums(self):
        updates = _dependabot()
        assert "uv" in updates, sorted(updates)
        assert updates["uv"].get("versioning-strategy") == "lockfile-only"

    def test_actions_updates_are_kept(self):
        assert "github-actions" in _dependabot()


# --- Import-group comments in the test files ----------------------------


GROUP_COMMENTS = {
    "standard library": re.compile(r"^\s*#\s*standard[ -]library\b", re.I),
    "third-party": re.compile(r"^\s*#\s*third[ -]party\b", re.I),
    "local": re.compile(r"^\s*#\s*local\b", re.I),
}
LOCAL_PACKAGES = {"tiredize", "tests"}


def _import_group(node: ast.stmt) -> str:
    if isinstance(node, ast.ImportFrom):
        top = (node.module or "").split(".")[0] if node.level == 0 else \
            "tests"
    else:
        top = node.names[0].name.split(".")[0]
    if top in LOCAL_PACKAGES:
        return "local"
    if top in sys.stdlib_module_names or top == "__future__":
        return "standard library"
    return "third-party"


def _test_files() -> list[Path]:
    return sorted(
        p for p in (REPO_ROOT / "tests").rglob("*.py")
        if p.name != "__init__.py"
    )


@pytest.mark.parametrize(
    "path", _test_files(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_every_import_group_has_its_comment(path):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    first_of_group: dict[str, ast.stmt] = {}
    for node in ast.parse(text).body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            first_of_group.setdefault(_import_group(node), node)
    missing = []
    for group, node in first_of_group.items():
        above = node.lineno - 2
        while above >= 0 and not lines[above].strip():
            above -= 1
        if above < 0 or not GROUP_COMMENTS[group].match(lines[above]):
            missing.append(f"line {node.lineno}: no `# {group}` comment")
    assert not missing, missing
