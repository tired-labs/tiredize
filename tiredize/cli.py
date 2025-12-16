from __future__ import annotations
from pathlib import Path
from tiredize.core_types import RuleResult
from tiredize.linter.engine import run_linter
from tiredize.markdown.types.document import Document
from typing import Any, Dict, List
import argparse
import sys
import yaml


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


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = yaml.safe_load(f) or {}
    return data


def _run_rules(
    doc: Document,
    rules_config_path: Path,
) -> List[RuleResult]:
    raw_config = _load_yaml(rules_config_path)

    results: List[RuleResult] = run_linter(
        document=doc,
        rule_configs=raw_config
    )
    return results


def _run_markdown_schema(doc: Document, schema_path: Path) -> List[RuleResult]:
    # Placeholder for now. Eventually this will:
    #   - load the markdown schema
    #   - compare Document.sections to provided schema
    #   - return RuleResults with appropriate rule_ids, e.g.
    #       "schema.markdown.missing_section"
    return []


def _run_frontmatter_schema(
        doc: Document,
        schema_path: Path) -> List[RuleResult]:
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
        doc.load(path=Path(path_str))

        all_results: List[RuleResult] = []

        if args.rules_path:
            all_results.extend(
                _run_rules(
                    doc, Path(args.rules_path)
                )
            )

        if args.markdown_schema_path:
            all_results.extend(
                _run_markdown_schema(
                    doc, Path(args.markdown_schema_path)
                )
            )

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
