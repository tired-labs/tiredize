# Standard library
from __future__ import annotations
from pathlib import Path

# Local
from tiredize.cli import main


# --- Argument validation (exit code 2) ---


def test_no_arguments(capsys):
    result = main([])
    assert result == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_paths_without_config(capsys, tmp_path):
    doc = tmp_path / "lonely_doc.md"
    doc.write_text("# Just Vibes\n")
    result = main([str(doc)])
    assert result == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_config_without_paths(capsys, tmp_path):
    schema = tmp_path / "orphan_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Title\n"
    )
    result = main(["--markdown-schema", str(schema)])
    assert result == 2
    captured = capsys.readouterr()
    assert "error:" in captured.err


# --- Happy path (exit code 0) ---


def test_valid_document_passes_schema(capsys, tmp_path):
    doc = tmp_path / "golden_ticket.md"
    doc.write_text("# Welcome\n\nNothing to see here.\n")
    schema = tmp_path / "chill_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Welcome\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc),
    ])
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_valid_document_passes_rules(capsys, tmp_path):
    doc = tmp_path / "squeaky_clean.md"
    doc.write_text("# Short Lines\n\nAll good here.\n")
    rules = tmp_path / "lenient_rules.yaml"
    rules.write_text(
        "line_length:\n"
        "  max_length: 80\n"
    )
    result = main([
        "--rules", str(rules),
        str(doc),
    ])
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == ""


# --- Validation errors (exit code 1) ---


def test_schema_violation_prints_errors(capsys, tmp_path):
    doc = tmp_path / "incomplete_essay.md"
    doc.write_text("# Introduction\n\nJust the intro.\n")
    schema = tmp_path / "demanding_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Introduction\n"
        "    sections:\n"
        "      - name: Background\n"
        "        level: 2\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "schema.markdown.missing_section" in captured.out


def test_invalid_schema_prints_error(capsys, tmp_path):
    doc = tmp_path / "innocent_bystander.md"
    doc.write_text("# Whatever\n")
    schema = tmp_path / "contradictory_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Whatever\n"
        "    pattern: '.+'\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_ambiguous_schema_prints_error(capsys, tmp_path):
    doc = tmp_path / "ambiguous_doc.md"
    doc.write_text(
        "# Report\n\n"
        "## Procedures\n\n"
    )
    schema = tmp_path / "ambiguous_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Report\n"
        "    sections:\n"
        "      - pattern: '.+'\n"
        "        level: 2\n"
        "        required: false\n"
        "      - name: Procedures\n"
        "        level: 2\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_unknown_rule_prints_error(capsys, tmp_path):
    doc = tmp_path / "rule_breaker.md"
    doc.write_text("# Doesn't Matter\n")
    rules = tmp_path / "fantasy_rules.yaml"
    rules.write_text(
        "the_rule_of_cool:\n"
        "  enabled: true\n"
    )
    result = main([
        "--rules", str(rules),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "the_rule_of_cool" in captured.err


# --- Multiple files ---


def test_multiple_files_all_clean(capsys, tmp_path):
    doc_a = tmp_path / "file_a.md"
    doc_a.write_text("# Alpha\n\nContent A.\n")
    doc_b = tmp_path / "file_b.md"
    doc_b.write_text("# Bravo\n\nContent B.\n")
    schema = tmp_path / "flexible_schema.yaml"
    schema.write_text(
        "allow_extra_sections: true\n"
        "sections:\n"
        "  - pattern: '.+'\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc_a), str(doc_b),
    ])
    assert result == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_multiple_files_one_violation(capsys, tmp_path):
    doc_clean = tmp_path / "pristine.md"
    doc_clean.write_text("# Shiny\n\nAll good.\n")
    doc_dirty = tmp_path / "messy.md"
    doc_dirty.write_text(
        "# Shiny\n\n# Bonus Round\n\nNot in schema.\n"
    )
    schema = tmp_path / "strict_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Shiny\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc_clean), str(doc_dirty),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert str(doc_dirty) in captured.out
    assert str(doc_clean) not in captured.out


# --- Output format ---


def test_output_format(capsys, tmp_path):
    doc = tmp_path / "format_check.md"
    doc.write_text(
        "# Report\n\n# Stowaway\n\nUnexpected.\n"
    )
    schema = tmp_path / "strict_format_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Report\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    lines = captured.out.strip().splitlines()
    assert len(lines) >= 1
    for line in lines:
        parts = line.split(": ", maxsplit=1)
        assert len(parts) == 2, f"Expected 'loc: msg' but got: {line}"
        location, message = parts
        loc_parts = location.split(":")
        assert len(loc_parts) == 3, (
            f"Expected 'path:line:col' but got: {location}"
        )
        path_str, line_num, col_num = loc_parts
        assert Path(path_str).name == "format_check.md"
        assert line_num.isdigit()
        assert col_num.isdigit()
        assert message.startswith("[")
        assert "] " in message


# --- File I/O errors (graceful handling) ---


def test_nonexistent_document_path(capsys, tmp_path):
    ghost = tmp_path / "does_not_exist.md"
    schema = tmp_path / "any_schema.yaml"
    schema.write_text(
        "sections:\n"
        "  - name: Phantom\n"
    )
    result = main([
        "--markdown-schema", str(schema),
        str(ghost),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_nonexistent_schema_path(capsys, tmp_path):
    doc = tmp_path / "real_doc.md"
    doc.write_text("# Real\n")
    ghost_schema = tmp_path / "vanished_schema.yaml"
    result = main([
        "--markdown-schema", str(ghost_schema),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err


def test_nonexistent_rules_path(capsys, tmp_path):
    doc = tmp_path / "real_doc.md"
    doc.write_text("# Real\n")
    ghost_rules = tmp_path / "vanished_rules.yaml"
    result = main([
        "--rules", str(ghost_rules),
        str(doc),
    ])
    assert result == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
