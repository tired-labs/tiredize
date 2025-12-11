# tiredize/rule_runner.py

from typing import Dict, Any, List
from tiredize.markdown.types.document import Document
from tiredize.linter.registry import RULES
from tiredize.types import RuleResult


def run_rules(document: Document, config: Dict[str, Any]) -> List[RuleResult]:
    results: List[RuleResult] = []

    rules_cfg = config.get("rules", {})

    for rule_id, func in RULES.items():
        rule_settings = rules_cfg.get(rule_id, {})
        enabled = bool(rule_settings.get("enabled", True))
        if not enabled:
            continue

        rule_results = func(document, config)
        results.extend(rule_results)

    return results
