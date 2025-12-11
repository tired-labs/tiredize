# tiredize/lint/rules/line_length.py

from typing import Dict, Any, List
from tiredize.markdown.types.document import Document
from tiredize.linter.types import Rule
from tiredize.linter.types import RuleResult


def validate_line_length(document: Document, config: Dict[str, Any]) -> List[RuleResult]:
    # Example stub, replace with your real logic
    results: List[RuleResult] = []
    lines = document.string_markdown.splitlines()

    max_len = int(config.get("line_length", {}).get("max", 120))

    for idx, line in enumerate(lines, start=1):
        if len(line) > max_len:
            # Construct a Position for the start of the line if you want to be precise
            results.append(
                RuleResult(
                    rule_id="line_length",
                    message=f"Line {idx} exceeds max length {max_len}",
                    position=None,  # or a real Position if you want
                )
            )

    return results


RULES = [
    Rule(
        id="line_length",
        description="Enforce maximum line length on markdown content.",
        func=validate_line_length,
    )
]
