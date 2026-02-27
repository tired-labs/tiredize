# Standard library
from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse
import sys

# Third-party
import yaml

# Local
from tiredize.core_types import RuleNotFoundError
from tiredize.core_types import RuleResult
from tiredize.linter.engine import run_linter
from tiredize.markdown.types.document import Document
from tiredize.markdown.types.schema import load_schema
from tiredize.validators.markdown_schema import AmbiguityError
from tiredize.validators.markdown_schema import validate


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiredize",
        description="Validate markdown documents against user-defined "
        "linting rules and schemas."
    )

    parser.add_argument(
        "--rules",
        dest="rules_path",
        help="YAML configuration file defining linter rules.",
    )
    parser.add_argument(
        "--markdown-schema",
        dest="markdown_schema_path",
        help="YAML configuration file defining markdown schema.",
    )
    parser.add_argument(
        "--frontmatter-schema",
        dest="frontmatter_schema_path",
        help="YAML configuration file defining frontmatter schema.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown files to validate.",
    )

    return parser


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    return data


def _run_rules(
    doc: Document,
    rules_config_path: Path,
) -> list[RuleResult]:
    raw_config = _load_yaml(rules_config_path)

    results: list[RuleResult] = run_linter(
        document=doc,
        rule_configs=raw_config
    )
    return results


def _run_markdown_schema(doc: Document, schema_path: Path) -> list[RuleResult]:
    schema = load_schema(schema_path.read_text())
    return validate(doc, schema)


def _run_frontmatter_schema(
        doc: Document,
        schema_path: Path) -> list[RuleResult]:
    # Placeholder for now. Eventually this will:
    #   - load the frontmatter schema
    #   - compare Document.frontmatter to provided schema
    #   - return RuleResults with appropriate rule_ids, e.g.
    #       "schema.frontmatter.missing_field"
    return []


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if not args.paths or not (
        args.rules_path or args.markdown_schema_path or
            args.frontmatter_schema_path):
        parser.print_usage(sys.stderr)
        print(
            "error: at least one of --rules, --markdown-schema, or "
            "--frontmatter-schema must be provided, and at least one path.",
            file=sys.stderr,
        )
        return 2

    exit_code = 0

    for path_str in args.paths:
        doc = Document()
        try:
            doc.load(path=Path(path_str))
        except FileNotFoundError as exc:
            print(
                f"error: {exc}",
                file=sys.stderr,
            )
            exit_code = 1
            continue

        all_results: list[RuleResult] = []

        if args.rules_path:
            try:
                all_results.extend(
                    _run_rules(
                        doc, Path(args.rules_path)
                    )
                )
            except (
                RuleNotFoundError,
                FileNotFoundError,
                yaml.YAMLError,
            ) as exc:
                print(
                    f"error: {exc}",
                    file=sys.stderr,
                )
                return 1

        if args.markdown_schema_path:
            try:
                all_results.extend(
                    _run_markdown_schema(
                        doc, Path(args.markdown_schema_path)
                    )
                )
            except (
                ValueError,
                AmbiguityError,
                FileNotFoundError,
                yaml.YAMLError,
            ) as exc:
                print(
                    f"error: {exc}",
                    file=sys.stderr,
                )
                return 1

        if args.frontmatter_schema_path:
            all_results.extend(
                _run_frontmatter_schema(
                    doc, Path(args.frontmatter_schema_path)
                )
            )

        for res in all_results:
            pos = res.position
            line, col = doc.line_col(pos.offset)
            print(f"{doc.path}:{line}:{col}: [{res.rule_id}] {res.message}")
        if all_results:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
