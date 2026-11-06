# Standard library
from __future__ import annotations
from pathlib import Path
import re

# Third party
import yaml


# Acceptance tests for the release workflow's contract (issue
# `pypi-release`, Release workflow criteria).
#
# Only GitHub can run a workflow, so these tests read
# `.github/workflows/release.yaml` as data and check its structure:
# triggers, job ordering through `needs`, environments, permissions,
# checkout depth and the publish action's inputs. They identify jobs by
# what they do, never by name:
#
# - a *publish job* has a step using `pypa/gh-action-pypi-publish`;
#   the TestPyPI and PyPI publish jobs are told apart by environment;
# - the *build job* is the one job uploading an artifact with
#   `actions/upload-artifact`;
# - a *pre-publish job* is the build job, or a job that downloads the
#   artifact and runs before both publish jobs.
#
# What this cannot check, and is left to review and to the user's
# v0.1.0 release: that the strict-tag guard's pattern accepts exactly
# `vX.Y.Z`, that the `main` check is correct, that the install check
# compares the printed version with the expected one, and that
# publishing through the registered Trusted Publishers succeeds. That
# `ci.yaml` is unchanged is a diff against `main` at verification, not
# a test, so the suite does not freeze `ci.yaml` for later work.


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
RELEASE = WORKFLOWS / "release.yaml"

PUBLISH_ACTION = "pypa/gh-action-pypi-publish@"
UPLOAD_ACTION = "actions/upload-artifact@"
DOWNLOAD_ACTION = "actions/download-artifact@"
CHECKOUT_ACTION = "actions/checkout@"
TESTPYPI_UPLOAD_URL = "https://test.pypi.org/legacy/"

BUILD_COMMANDS = (
    "python -m build",
    "python3 -m build",
    "pyproject-build",
    "pip wheel",
    "hatch build",
    "uv build",
)


# --- Reading the workflow ---------------------------------------------


def _workflow_text() -> str:
    assert RELEASE.is_file(), f"{RELEASE.relative_to(REPO_ROOT)} is missing"
    return RELEASE.read_text(encoding="utf-8")


def _workflow() -> dict:
    data = yaml.safe_load(_workflow_text())
    assert isinstance(data, dict), "release.yaml is not a mapping"
    return data


def _triggers(workflow: dict) -> dict:
    # YAML 1.1 reads a bare `on` key as the boolean True.
    on = workflow.get("on", workflow.get(True))
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {name: None for name in on}
    assert isinstance(on, dict), f"unreadable triggers: {on!r}"
    return on


def _jobs(workflow: dict) -> dict:
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict) and jobs, "release.yaml has no jobs"
    return jobs


def _needs(job: dict) -> list[str]:
    needs = job.get("needs", [])
    return [needs] if isinstance(needs, str) else list(needs)


def _ancestors(jobs: dict, name: str) -> set[str]:
    """Every job `name` waits for, directly or transitively."""
    seen: set[str] = set()
    pending = list(_needs(jobs[name]))
    while pending:
        parent = pending.pop()
        if parent not in seen:
            seen.add(parent)
            pending.extend(_needs(jobs[parent]))
    return seen


def _steps(job: dict) -> list[dict]:
    return job.get("steps", []) or []


def _uses(step: dict) -> str:
    return str(step.get("uses", ""))


def _run(step: dict) -> str:
    return str(step.get("run", ""))


def _job_runs(job: dict) -> str:
    return "\n".join(_run(step) for step in _steps(job))


def _has_step(job: dict, action: str) -> bool:
    return any(_uses(step).startswith(action) for step in _steps(job))


def _environment(job: dict) -> str | None:
    environment = job.get("environment")
    if isinstance(environment, dict):
        return environment.get("name")
    return environment


def _publish_jobs(jobs: dict) -> dict:
    return {
        name: job for name, job in jobs.items()
        if _has_step(job, PUBLISH_ACTION)
    }


def _publish_job(jobs: dict, environment: str) -> str:
    matches = [
        name for name, job in _publish_jobs(jobs).items()
        if _environment(job) == environment
    ]
    assert len(matches) == 1, (
        f"expected one publish job in environment {environment!r}, "
        f"got {matches}"
    )
    return matches[0]


def _publish_step(job: dict) -> dict:
    steps = [s for s in _steps(job) if _uses(s).startswith(PUBLISH_ACTION)]
    assert len(steps) == 1, "expected one publish step per publish job"
    return steps[0]


def _build_job(jobs: dict) -> str:
    uploaders = [
        name for name, job in jobs.items() if _has_step(job, UPLOAD_ACTION)
    ]
    assert len(uploaders) == 1, (
        f"expected exactly one job uploading the artifact, got {uploaders}"
    )
    return uploaders[0]


def _pre_publish_jobs(jobs: dict) -> list[str]:
    build = _build_job(jobs)
    before_both = set.intersection(*(
        _ancestors(jobs, name) for name in _publish_jobs(jobs)
    )) if _publish_jobs(jobs) else set()
    return [build] + [
        name for name in before_both
        if name != build and _has_step(jobs[name], DOWNLOAD_ACTION)
    ]


def _builds(job: dict) -> bool:
    runs = _job_runs(job)
    return any(command in runs for command in BUILD_COMMANDS)


def _steps_before_first_build(job: dict) -> list[dict]:
    before = []
    for step in _steps(job):
        if any(command in _run(step) for command in BUILD_COMMANDS):
            break
        if _uses(step).startswith(UPLOAD_ACTION):
            break
        before.append(step)
    return before


def _gate_steps(
    jobs: dict, pattern: str, whole_step: bool = False
) -> list[dict]:
    """Steps matching `pattern` that run before anything is built.

    The pattern is searched in the step's `run` script, or with
    `whole_step` in everything the step says (its `env`, `if`, `with`).
    """
    build = _build_job(jobs)
    candidates = [
        step for name in _ancestors(jobs, build)
        for step in _steps(jobs[name])
    ] + _steps_before_first_build(jobs[build])

    def text(step: dict) -> str:
        return yaml.safe_dump(step) if whole_step else _run(step)
    return [s for s in candidates if re.search(pattern, text(s))]


def _grants_id_token(permissions) -> bool:
    if permissions == "write-all":
        return True
    if isinstance(permissions, dict):
        return permissions.get("id-token") == "write"
    return False


# --- Files ------------------------------------------------------------


class TestWorkflowFiles:
    def test_release_workflow_has_the_registered_name(self):
        assert RELEASE.is_file()

    def test_testpypi_workflow_is_deleted(self):
        assert not (WORKFLOWS / "release-testpypi.yml").exists()

    def test_release_workflow_is_the_only_publisher(self):
        publishers = sorted(
            path.name for path in WORKFLOWS.iterdir()
            if path.suffix in {".yml", ".yaml"}
            and "pypa/gh-action-pypi-publish" in path.read_text("utf-8")
        )
        assert publishers == ["release.yaml"]


# --- Triggers ---------------------------------------------------------


class TestTriggers:
    def test_triggers_are_manual_run_and_tag_push(self):
        assert set(_triggers(_workflow())) == {"workflow_dispatch", "push"}

    def test_push_trigger_is_every_v_tag_only(self):
        # Every `v*` tag must start the run, so that a malformed one
        # reaches the strict-tag guard and fails rather than being
        # silently ignored. Branch pushes must not start it.
        push = _triggers(_workflow())["push"]
        assert isinstance(push, dict)
        assert set(push) == {"tags"}
        tags = push["tags"]
        assert (tags == "v*") or ("v*" in tags)


# --- Lint and tests gate everything -----------------------------------


class TestGate:
    def test_lint_runs_before_anything_is_built(self):
        steps = _gate_steps(_jobs(_workflow()), r"\bflake8\b")
        assert steps, "no flake8 step runs before the build"
        assert any(
            re.search(r"\bflake8\b.*\btiredize\b.*\btests\b", _run(s))
            for s in steps
        ), "flake8 does not cover both tiredize and tests"

    def test_full_test_suite_runs_before_anything_is_built(self):
        steps = _gate_steps(_jobs(_workflow()), r"\bpytest\b")
        assert steps, "no pytest step runs before the build"
        for step in steps:
            for narrowing in ("-k", "-m", "--deselect", "--ignore"):
                assert not re.search(
                    rf"\bpytest\b.*\s{re.escape(narrowing)}\b", _run(step)
                ), f"pytest is narrowed with {narrowing}"

    def test_gate_failures_are_not_ignored(self):
        workflow = _workflow()
        jobs = _jobs(workflow)
        build = _build_job(jobs)
        for name in _ancestors(jobs, build) | {build}:
            assert not jobs[name].get("continue-on-error"), name
        for step in _gate_steps(jobs, r"\b(flake8|pytest)\b"):
            assert not step.get("continue-on-error"), _run(step)

    def test_every_publish_job_waits_for_the_build(self):
        jobs = _jobs(_workflow())
        build = _build_job(jobs)
        publishers = _publish_jobs(jobs)
        assert publishers
        for name in publishers:
            assert build in _ancestors(jobs, name), name


# --- Checkout ---------------------------------------------------------


class TestCheckout:
    def test_every_checkout_fetches_full_history(self):
        checkouts = [
            step for job in _jobs(_workflow()).values()
            for step in _steps(job)
            if _uses(step).startswith(CHECKOUT_ACTION)
        ]
        assert checkouts
        for step in checkouts:
            depth = (step.get("with") or {}).get("fetch-depth")
            assert str(depth) == "0", step


# --- Build once, check, smoke-test, hand over -------------------------


class TestBuildOnce:
    def test_only_the_build_job_builds(self):
        jobs = _jobs(_workflow())
        build = _build_job(jobs)
        builders = [name for name, job in jobs.items() if _builds(job)]
        assert builders in ([], [build]), builders

    def test_publish_jobs_download_the_artifact(self):
        publishers = _publish_jobs(_jobs(_workflow()))
        assert publishers
        for name, job in publishers.items():
            assert _has_step(job, DOWNLOAD_ACTION), name
            assert not _builds(job), name

    def test_distributions_pass_a_metadata_check(self):
        jobs = _jobs(_workflow())
        runs = "\n".join(
            _job_runs(jobs[name]) for name in _pre_publish_jobs(jobs)
        )
        assert re.search(r"\btwine\b.*\bcheck\b", runs)

    def test_built_wheel_runs_version_in_a_clean_environment(self):
        jobs = _jobs(_workflow())
        runs = "\n".join(
            _job_runs(jobs[name]) for name in _pre_publish_jobs(jobs)
        )
        assert "tiredize --version" in runs
        assert re.search(r"\bvenv\b", runs), "no clean environment"


# --- Manual runs reach TestPyPI only ----------------------------------


class TestManualRun:
    def test_testpypi_publish_uses_testpypi_environment(self):
        jobs = _jobs(_workflow())
        job = jobs[_publish_job(jobs, "testpypi")]
        inputs = _publish_step(job).get("with") or {}
        assert inputs.get("repository-url") == TESTPYPI_UPLOAD_URL

    def test_pypi_publish_is_limited_to_tag_pushes(self):
        # A manual run can be started on a tag ref, so only the event
        # name tells a manual run from a tag push.
        jobs = _jobs(_workflow())
        testpypi = _publish_job(jobs, "testpypi")
        pypi = _publish_job(jobs, "pypi")
        shared = _ancestors(jobs, testpypi) | {testpypi}
        own_path = (_ancestors(jobs, pypi) | {pypi}) - shared
        conditions = [str(jobs[name].get("if", "")) for name in own_path]
        assert any(
            "github.event_name" in condition and "push" in condition
            for condition in conditions
        ), conditions


# --- Tag pushes: TestPyPI, install check, approval, PyPI --------------


class TestTagPush:
    def test_testpypi_publish_skips_existing_versions(self):
        jobs = _jobs(_workflow())
        job = jobs[_publish_job(jobs, "testpypi")]
        inputs = _publish_step(job).get("with") or {}
        assert inputs.get("skip-existing") is True

    def test_testpypi_install_check_sits_between_the_publishes(self):
        jobs = _jobs(_workflow())
        testpypi = _publish_job(jobs, "testpypi")
        pypi = _publish_job(jobs, "pypi")
        checks = [
            name for name in _ancestors(jobs, pypi)
            if testpypi in _ancestors(jobs, name)
            and "test.pypi.org" in _job_runs(jobs[name])
            and "tiredize --version" in _job_runs(jobs[name])
        ]
        assert checks, "no TestPyPI install check between the publishes"
        for name in checks:
            runs = _job_runs(jobs[name])
            assert "tiredize==" in runs, "install is not pinned"
            # Dependencies come from pypi.org only: mixing indexes would
            # let TestPyPI supply them.
            assert "--extra-index-url" not in runs
            assert re.search(r"\bvenv\b", runs), "no clean environment"

    def test_pypi_publish_uses_pypi_environment(self):
        jobs = _jobs(_workflow())
        job = jobs[_publish_job(jobs, "pypi")]
        inputs = _publish_step(job).get("with") or {}
        assert inputs.get("repository-url") in (
            None, "https://upload.pypi.org/legacy/"
        )

    def test_strict_tag_guard_runs_before_anything_is_built(self):
        jobs = _jobs(_workflow())
        guards = _gate_steps(
            jobs, r"github\.ref|GITHUB_REF", whole_step=True
        )
        assert guards, "no step checks the tag before the build"

    def test_pypi_publish_checks_the_commit_is_on_main(self):
        jobs = _jobs(_workflow())
        pypi = _publish_job(jobs, "pypi")
        runs = "\n".join(
            _job_runs(jobs[name]) for name in _ancestors(jobs, pypi) | {pypi}
        )
        assert re.search(r"\b(origin/main|refs/heads/main)\b", runs)


# --- Trusted Publishing -----------------------------------------------


class TestTrustedPublishing:
    def test_publishers_match_the_registered_environments(self):
        publishers = _publish_jobs(_jobs(_workflow()))
        environments = sorted(
            str(_environment(job)) for job in publishers.values()
        )
        assert environments == ["pypi", "testpypi"]

    def test_publish_steps_pass_no_credentials(self):
        for name, job in _publish_jobs(_jobs(_workflow())).items():
            inputs = _publish_step(job).get("with") or {}
            assert "password" not in inputs, name
            assert "user" not in inputs, name

    def test_workflow_references_no_secrets(self):
        assert "secrets." not in _workflow_text()

    def test_id_token_write_only_on_publish_jobs(self):
        workflow = _workflow()
        jobs = _jobs(workflow)
        assert not _grants_id_token(workflow.get("permissions"))
        publishers = _publish_jobs(jobs)
        assert publishers
        for name, job in jobs.items():
            granted = _grants_id_token(job.get("permissions"))
            assert granted == (name in publishers), name
