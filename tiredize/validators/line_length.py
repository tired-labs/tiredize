from tiredize.document import Document
from tiredize.types import RuleResult
from typing import List, Dict


def validate_line_length(doc: Document, schema: Dict) -> List[RuleResult]:
    """
    Enforce document line length and whitespace rules based on the provided
    schema.

    Expected schema fragment:

    line_length:
      max: 120
      ignore_code_blocks: true
      ignore_tables: true
      ignore_urls: true
    """
    cfg = schema.get("line_length", {})
    cfg_ignore_code = bool(cfg.get("ignore_code_blocks", True))
    # cfg_ignore_tables = bool(cfg.get("ignore_tables", True))
    # cfg_ignore_urls = bool(cfg.get("ignore_urls", True))
    cfg_max_len = int(cfg.get("max", 120))

    results: List[RuleResult] = []

    for i, line in enumerate(doc.lines, start=1):
        if cfg_ignore_code and i in doc.fenced_lines:
            continue

        # You already have RE_TABLE_ROW and RE_TABLE_DIV, but they live in
        # document.py. For now, keep it simple and do not special case tables
        # until you decide whether you want those regexes shared or moved. Same
        # for URL detection; we can refine this later.

        if len(line) > cfg_max_len:
            results.append(
                RuleResult(
                    rule_id="line_length",
                    line=i,
                    message=f"Line length {len(line)} exceeds max "
                    "{cfg_max_len}",
                )
            )

    return results
