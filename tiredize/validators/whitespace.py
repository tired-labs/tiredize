from tiredize.document import Document
from tiredize.types import RuleResult
from typing import List, Dict


def validate_whitespace(doc: Document, schema: Dict) -> List[RuleResult]:
    """
    Enforce document whitespace rules based on the provided schema.

    Expected schema fragment:

    whitespace:
      ignore_code_blocks: true
      trailing_ws: true
      tab_char: true
    """
    cfg = schema.get("whitespace", {})
    cfg_ignore_code = bool(cfg.get("ignore_code_blocks", True))
    cfg_trailing_ws = bool(cfg.get("trailing_ws", True))
    cfg_tab_char = bool(cfg.get("tab_char", True))

    results: List[RuleResult] = []

    for i, line in enumerate(doc.lines, start=1):
        if cfg_ignore_code and i in doc.fenced_lines:
            continue

        if cfg_trailing_ws and line.rstrip() != line:
            results.append(
                RuleResult(
                    rule_id="trailing_ws",
                    line=i,
                    message="Trailing whitespace",
                )
            )

        if cfg_tab_char and "\t" in line:
            results.append(
                RuleResult(
                    rule_id="tab_char",
                    line=i,
                    message="Tab character found, use spaces",
                )
            )

    return results
