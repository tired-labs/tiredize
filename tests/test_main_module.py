# Standard library
from __future__ import annotations
from pathlib import Path
import shutil
import subprocess
import sys

# Third party
import pytest


# Acceptance tests for the `python -m tiredize` exit-status contract.
#
# These are black-box tests. They derive entirely from the Public
# Contract section of `.context/issues/main-module-exit-code.md` and
# exercise the two public entry points as subprocesses. They know
# nothing about how `tiredize/__main__.py` is written.
#
# The exit status of `python -m tiredize` is only observable from
# another process — importing `tiredize.__main__` runs `main()` at
# import time and yields no process status to assert on — so every
# test here spawns a subprocess with `cwd` at the repository root.
#
# `sys.executable` is used rather than a literal "python": many systems
# ship only `python3`, and the machine this suite was authored on is one
# of them.


REPO_ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER_SCHEMA = (
    REPO_ROOT / ".context" / "schemas" / "issue-frontmatter.yaml"
)
MARKDOWN_SCHEMA = (
    REPO_ROOT / ".context" / "schemas" / "issue-markdown.yaml"
)
RULES_PACKAGE = REPO_ROOT / "tiredize" / "linter" / "rules"

# One valid configuration body per built-in rule. Each supplies every
# key the rule could plausibly require, so when a case appends a fault
# the fault is the only thing wrong with the block.
BASELINE_RULE_CONFIGS = {
    "elements": "  disallow: [table]\n",
    "line_length": "  maximum_length: 200\n",
    "links": "  validate: false\n",
    "tabs": "  allowed: true\n",
    "trailing_whitespace": "  allowed: true\n",
    "unicode": "  allowed: true\n",
}

# One key per built-in rule, holding a value of the wrong type. Each
# key is one the rule accepts, so these exercise the wrong-type state
# rather than the unknown-key state, whether the key is required or
# optional.
WRONG_TYPED_RULE_CONFIGS = {
    "elements": ("disallow", "  disallow: table\n"),
    "line_length": (
        "maximum_length", "  maximum_length: forty winks\n"
    ),
    "links": ("validate", "  validate: yes please\n"),
    "tabs": ("allowed", "  allowed: sure thing\n"),
    "trailing_whitespace": (
        "allowed", "  allowed: sure thing\n"
    ),
    "unicode": ("allowed", "  allowed: sure thing\n"),
}

# Tests below assert the contract, not today's behaviour. They fail
# until the fix lands; see the tracking issue named in this reason.
PENDING = (
    "Pending the fix in .context/issues/main-module-exit-code.md; "
    "remove this skip when the fix lands."
)


def _console_script() -> str:
    """Absolute path to the installed `tiredize` console script."""
    path = shutil.which("tiredize")
    if path is None:
        pytest.skip("the tiredize console script is not on PATH")
    return path


def _issue_frontmatter(assignee: str) -> str:
    """A minimal issue frontmatter block naming `assignee`."""
    return (
        "---\n"
        f"assignee: {assignee}\n"
        "created: 2026-09-05\n"
        "knowledge: []\n"
        "priority: low\n"
        "status: draft\n"
        "tags: [tea, biscuits]\n"
        "type: spike\n"
        "workflow: software-engineering\n"
        "---\n"
        "\n"
        "# Tea Break Protocol\n"
    )


def _rule_modules() -> set[str]:
    """The built-in rule ids, read from the package directory.

    A rule id is the module filename and a module whose name starts
    with an underscore is not a rule — both are documented conventions
    in `.context/specifications/linter.md`. Reading the directory
    rather than calling `discover_rules()` keeps this suite black-box.
    """
    return {
        path.stem
        for path in RULES_PACKAGE.glob("*.py")
        if not path.stem.startswith("_")
    }


def _run_console(args: list[str]) -> subprocess.CompletedProcess:
    """Run the `tiredize` console script from the repository root."""
    return subprocess.run(
        [_console_script(), *args],
        capture_output=True,
        cwd=REPO_ROOT,
        text=True,
    )


def _run_module(args: list[str]) -> subprocess.CompletedProcess:
    """Run `python -m tiredize` from the repository root."""
    return subprocess.run(
        [sys.executable, "-m", "tiredize", *args],
        capture_output=True,
        cwd=REPO_ROOT,
        text=True,
    )


def _write_clean_document(directory: Path) -> Path:
    """A document that satisfies the markdown schema below."""
    doc = directory / "nap_time.md"
    doc.write_text("# Nap Time\n\nZzz.\n")
    return doc


def _write_dirty_document(directory: Path) -> Path:
    """A document with one unexpected section — a schema finding."""
    doc = directory / "caffeine_crash.md"
    doc.write_text(
        "# Nap Time\n\n# Espresso Shot\n\nWide awake.\n"
    )
    return doc


def _write_frontmatter_schema(directory: Path) -> Path:
    schema = directory / "paperwork.yaml"
    schema.write_text(
        "fields:\n"
        "  title:\n"
        "    type: string\n"
    )
    return schema


def _write_markdown_schema(directory: Path) -> Path:
    schema = directory / "sleepy_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Nap Time\n"
    )
    return schema


def _write_rule_config(directory: Path, body: str) -> Path:
    """Write an arbitrary rules configuration file."""
    rules = directory / "questionable_rules.yaml"
    rules.write_text(body)
    return rules


def _write_rules_config(directory: Path) -> Path:
    rules = directory / "no_rambling.yaml"
    rules.write_text(
        "line_length:\n"
        "  maximum_length: 10\n"
    )
    return rules


class TestExitStatus:
    """`python -m tiredize` exits with what `main()` returns.

    Contract: `0` when every path loaded and produced no findings, `1`
    on findings or a runtime error, `2` on a usage error. Findings do
    not stop the run; runtime errors do.
    """

    # --- Clean input (exit 0) ---

    def test_clean_document_exits_zero(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(doc),
        ])
        assert result.returncode == 0
        assert "no issues found" in result.stdout

    def test_several_clean_documents_exit_zero(self, tmp_path):
        first = _write_clean_document(tmp_path)
        second = tmp_path / "second_nap.md"
        second.write_text("# Nap Time\n\nMore Zzz.\n")
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(first), str(second),
        ])
        assert result.returncode == 0
        assert result.stdout.count("no issues found") == 2

    # --- Findings (exit 1) ---

    @pytest.mark.skip(reason=PENDING)
    def test_markdown_schema_finding_exits_one(self, tmp_path):
        doc = _write_dirty_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(doc),
        ])
        assert result.returncode == 1
        assert "schema.markdown." in result.stdout

    @pytest.mark.skip(reason=PENDING)
    def test_linter_rule_finding_exits_one(self, tmp_path):
        doc = tmp_path / "rambling_monologue.md"
        doc.write_text(
            "# Nap Time\n\nThis line goes on rather a lot longer.\n"
        )
        rules = _write_rules_config(tmp_path)
        result = _run_module([
            "--rules", str(rules),
            str(doc),
        ])
        assert result.returncode == 1
        assert "[line_length]" in result.stdout

    @pytest.mark.skip(reason=PENDING)
    def test_frontmatter_schema_finding_exits_one(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        schema = _write_frontmatter_schema(tmp_path)
        result = _run_module([
            "--frontmatter-schema", str(schema),
            str(doc),
        ])
        assert result.returncode == 1
        assert "schema.frontmatter." in result.stdout

    @pytest.mark.skip(reason=PENDING)
    def test_findings_do_not_stop_the_run(self, tmp_path):
        """Every path is processed even after a finding."""
        dirty = _write_dirty_document(tmp_path)
        clean = _write_clean_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(dirty), str(clean),
        ])
        assert result.returncode == 1
        assert str(dirty) in result.stdout
        assert f"{clean}: no issues found." in result.stdout

    # --- Runtime errors (exit 1) ---

    @pytest.mark.skip(reason=PENDING)
    def test_missing_configuration_file_exits_one(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        result = _run_module([
            "--markdown-schema", str(tmp_path / "abducted_schema.yaml"),
            str(doc),
        ])
        assert result.returncode == 1
        assert "error:" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_unknown_rule_id_exits_one(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        rules = tmp_path / "fantasy_rules.yaml"
        rules.write_text(
            "the_rule_of_cool:\n"
            "  enabled: true\n"
        )
        result = _run_module([
            "--rules", str(rules),
            str(doc),
        ])
        assert result.returncode == 1
        assert "the_rule_of_cool" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_missing_document_exits_one(self, tmp_path):
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(tmp_path / "phantom_thread.md"),
        ])
        assert result.returncode == 1
        assert "error:" in result.stderr

    # --- Usage errors (exit 2) ---

    @pytest.mark.skip(reason=PENDING)
    def test_no_arguments_exits_two(self):
        result = _run_module([])
        assert result.returncode == 2
        assert "error:" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_paths_without_configuration_exit_two(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        result = _run_module([str(doc)])
        assert result.returncode == 2
        assert "error:" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_configuration_without_paths_exits_two(self, tmp_path):
        schema = _write_markdown_schema(tmp_path)
        result = _run_module(["--markdown-schema", str(schema)])
        assert result.returncode == 2
        assert "error:" in result.stderr

    def test_unknown_flag_exits_two(self, tmp_path):
        """Argparse raises SystemExit(2) from inside main().

        This path is already correct today and must stay correct.
        """
        doc = _write_clean_document(tmp_path)
        result = _run_module(["--bogus", str(doc)])
        assert result.returncode == 2
        assert "usage:" in result.stderr

    # --- Runtime errors abort the run ---

    @pytest.mark.skip(reason=PENDING)
    def test_module_aborts_after_missing_document(self, tmp_path):
        """A missing earlier path leaves later paths unprocessed."""
        missing = tmp_path / "phantom_thread.md"
        later = _write_clean_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        result = _run_module([
            "--markdown-schema", str(schema),
            str(missing), str(later),
        ])
        assert result.returncode == 1
        assert "error:" in result.stderr
        assert str(later) not in result.stdout
        assert "no issues found" not in result.stdout

    @pytest.mark.skip(reason=PENDING)
    def test_console_script_aborts_after_missing_document(
        self, tmp_path
    ):
        """The abort rule applies to the console script too."""
        missing = tmp_path / "phantom_thread.md"
        later = _write_clean_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        result = _run_console([
            "--markdown-schema", str(schema),
            str(missing), str(later),
        ])
        assert result.returncode == 1
        assert "error:" in result.stderr
        assert str(later) not in result.stdout
        assert "no issues found" not in result.stdout


class TestStreamParity:
    """The two entry points are indistinguishable from the outside.

    For any argument list, `python -m tiredize` and `tiredize` must
    produce the same stdout, the same stderr, and the same exit status.
    """

    def test_parity_for_clean_document(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        args = ["--markdown-schema", str(schema), str(doc)]
        module = _run_module(args)
        console = _run_console(args)
        assert module.returncode == console.returncode
        assert module.stdout == console.stdout
        assert module.stderr == console.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_parity_for_findings(self, tmp_path):
        doc = _write_dirty_document(tmp_path)
        schema = _write_markdown_schema(tmp_path)
        args = ["--markdown-schema", str(schema), str(doc)]
        module = _run_module(args)
        console = _run_console(args)
        assert module.returncode == console.returncode
        assert module.stdout == console.stdout
        assert module.stderr == console.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_parity_for_runtime_error(self, tmp_path):
        doc = _write_clean_document(tmp_path)
        args = [
            "--markdown-schema", str(tmp_path / "abducted_schema.yaml"),
            str(doc),
        ]
        module = _run_module(args)
        console = _run_console(args)
        assert module.returncode == console.returncode
        assert module.stdout == console.stdout
        assert module.stderr == console.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_parity_for_usage_error(self):
        module = _run_module([])
        console = _run_console([])
        assert module.returncode == console.returncode
        assert module.stdout == console.stdout
        assert module.stderr == console.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_parity_for_non_ascii_findings(self, tmp_path):
        """Emoji and accents must not disturb either stream."""
        doc = tmp_path / "cafe_au_lait.md"
        doc.write_text(
            "# Nap Time \U0001f634\n\nCafé au lait ☕, sipped slowly.\n",
            encoding="utf-8",
        )
        rules = _write_rules_config(tmp_path)
        args = ["--rules", str(rules), str(doc)]
        module = _run_module(args)
        console = _run_console(args)
        assert module.returncode == console.returncode
        assert module.stdout == console.stdout
        assert module.stderr == console.stderr
        assert "[line_length]" in module.stdout


class TestIssueAssigneeVocabulary:
    """The project's own issue frontmatter schema names functions.

    Every allowed `assignee` value matches a function filename;
    `program-manager` replaces the lone exception, `PM`. These run the
    console script because it is what CI and the pre-commit hook use to
    validate `.context/issues/`, and its exit status is already correct.
    """

    def test_program_manager_is_allowed(self, tmp_path):
        doc = tmp_path / "tea_break.md"
        doc.write_text(_issue_frontmatter("program-manager"))
        result = _run_console([
            "--frontmatter-schema", str(FRONTMATTER_SCHEMA),
            str(doc),
        ])
        assert result.returncode == 0
        assert "no issues found" in result.stdout

    def test_pm_is_no_longer_allowed(self, tmp_path):
        """`program-manager` replaces `PM` rather than joining it.

        Reading of "in place of `PM`" in acceptance criterion 7; see
        the qa-engineer comment on the tracking issue.
        """
        doc = tmp_path / "old_habits.md"
        doc.write_text(_issue_frontmatter("PM"))
        result = _run_console([
            "--frontmatter-schema", str(FRONTMATTER_SCHEMA),
            str(doc),
        ])
        assert result.returncode == 1
        assert "schema.frontmatter.value_not_allowed" in result.stdout

    def test_every_issue_file_validates_clean(self):
        """The repository's own issues must stay valid.

        Unskipped: this passes today and guards the schema change —
        swapping the allowed value without updating
        `context-process-migration.md` breaks it.
        """
        issues = sorted(
            (REPO_ROOT / ".context" / "issues").glob("*.md")
        )
        assert issues, "expected issue files under .context/issues/"
        result = _run_console([
            "--markdown-schema", str(MARKDOWN_SCHEMA),
            "--frontmatter-schema", str(FRONTMATTER_SCHEMA),
            *[str(path) for path in issues],
        ])
        assert result.returncode == 0, result.stdout + result.stderr


class TestRuleConfigurationValidation:
    """An invalid rule configuration is a runtime error.

    Contract: three states are errors — a key the rule does not
    accept, a key the rule accepts holding a value of the wrong type,
    and a required key omitted. Each prints to stderr naming the rule
    id and the offending key, exits `1`, and aborts the run. An
    omitted optional key stays legal.

    These run the console script rather than `python -m tiredize`.
    The behaviour under test lives in the linter, not in the `-m`
    plumbing, and the console script's exit status is already correct
    today — so a failure here is attributable to rule-configuration
    validation and not to the exit-code defect this issue also fixes.
    That both entry points report it identically is covered by
    `TestStreamParity`.
    """

    # --- The three error states, on a rule with an unambiguous
    # --- required key (`maximum_length`) and an unambiguous optional
    # --- one (`exclude`).

    @pytest.mark.skip(reason=PENDING)
    def test_unknown_key_is_an_error(self, tmp_path):
        """`max_length` is not a key `line_length` accepts.

        The real-world instance: `tests/test_cli.py` configures this
        exact typo, so the rule silently never runs.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  maximum_length: 200\n"
            "  max_length: 80\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert "line_length" in result.stderr
        assert "max_length" in result.stderr
        assert "no issues found" not in result.stdout

    @pytest.mark.skip(reason=PENDING)
    def test_required_key_with_wrong_type_is_an_error(self, tmp_path):
        """`maximum_length` wants an integer, not a string."""
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  maximum_length: forty winks\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert "line_length" in result.stderr
        assert "maximum_length" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_optional_key_with_wrong_type_is_an_error(self, tmp_path):
        """`exclude` wants a list, not a bare string.

        Optional does not mean unchecked: a key the rule accepts is
        an error when its value is of the wrong type, whether or not
        the rule requires it.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  maximum_length: 200\n"
            "  exclude: code_block\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert "line_length" in result.stderr
        assert "exclude" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_required_key_omitted_is_an_error(self, tmp_path):
        """`line_length` cannot run without `maximum_length`.

        Required is derived from the rule's existing behaviour: the
        rule reads the key and produces nothing when it is absent.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  exclude: [code_block]\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert "line_length" in result.stderr
        assert "maximum_length" in result.stderr

    @pytest.mark.skip(reason=PENDING)
    def test_unicode_required_key_omitted_is_an_error(self, tmp_path):
        """A second rule with an unambiguously required key.

        `unicode` reads `allowed` and produces nothing when it is
        absent, the same shape as `line_length.maximum_length`.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "unicode:\n"
            "  exclude: [code_block]\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert "unicode" in result.stderr
        assert "allowed" in result.stderr

    # --- The negative case: optional keys stay optional ---

    def test_omitted_optional_key_is_not_an_error(self, tmp_path):
        """`exclude` may be left out; that is not a fault.

        Unskipped: it passes today and guards the other direction —
        validation that demanded every documented key would break it.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  maximum_length: 200\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 0, (
            result.stdout + result.stderr
        )
        assert "no issues found" in result.stdout

    # --- An invalid configuration aborts the run ---

    @pytest.mark.skip(reason=PENDING)
    def test_invalid_configuration_aborts_the_run(self, tmp_path):
        """A later path goes unprocessed and is never reported."""
        first = _write_clean_document(tmp_path)
        second = tmp_path / "second_nap.md"
        second.write_text("# Nap Time\n\nMore Zzz.\n")
        rules = _write_rule_config(
            tmp_path,
            "line_length:\n"
            "  maximum_length: 200\n"
            "  max_length: 80\n",
        )
        result = _run_console([
            "--rules", str(rules),
            str(first), str(second),
        ])
        assert result.returncode == 1
        assert "line_length" in result.stderr
        assert "max_length" in result.stderr
        assert str(second) not in result.stdout
        assert "no issues found" not in result.stdout

    # --- Every built-in rule validates its configuration ---

    @pytest.mark.skip(reason=PENDING)
    @pytest.mark.parametrize(
        "rule_id", sorted(BASELINE_RULE_CONFIGS)
    )
    def test_unknown_key_is_an_error_for_every_rule(
        self, rule_id, tmp_path
    ):
        """No rule may quietly swallow a key it does not accept.

        The baseline block is a valid configuration for the rule, so
        the appended key is the only fault and the case holds whether
        the baseline keys are required or optional.
        """
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(
            tmp_path,
            f"{rule_id}:\n"
            + BASELINE_RULE_CONFIGS[rule_id]
            + "  snooze_button: true\n",
        )
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert rule_id in result.stderr
        assert "snooze_button" in result.stderr
        assert "no issues found" not in result.stdout

    @pytest.mark.skip(reason=PENDING)
    @pytest.mark.parametrize(
        "rule_id", sorted(WRONG_TYPED_RULE_CONFIGS)
    )
    def test_wrong_typed_value_is_an_error_for_every_rule(
        self, rule_id, tmp_path
    ):
        """No rule may treat a wrong-typed value as absent."""
        key, body = WRONG_TYPED_RULE_CONFIGS[rule_id]
        doc = _write_clean_document(tmp_path)
        rules = _write_rule_config(tmp_path, f"{rule_id}:\n" + body)
        result = _run_console(["--rules", str(rules), str(doc)])
        assert result.returncode == 1
        assert rule_id in result.stderr
        assert key in result.stderr
        assert "no issues found" not in result.stdout

    def test_every_rule_module_has_a_configuration_case(self):
        """A new rule cannot be added without a case here.

        Unskipped: this passes today and is the guard that gives the
        "a new rule author cannot omit it by accident" intent teeth —
        dropping a module into `tiredize/linter/rules/` without
        adding it to both maps above breaks this test.
        """
        modules = _rule_modules()
        assert modules, "expected rule modules in the rules package"
        assert modules == set(BASELINE_RULE_CONFIGS)
        assert modules == set(WRONG_TYPED_RULE_CONFIGS)
