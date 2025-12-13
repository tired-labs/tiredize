from __future__ import annotations
from dataclasses import replace
from tiredize.core_types import RuleResult
from tiredize.linter.rules import Rule, discover_rules
from tiredize.markdown.types.document import Document
from typing import Any
from typing import Dict
from typing import List


def _select_rules(
    rules: Dict[str, Rule],
    rule_configs: Dict[str, Dict[str, Dict[str, Any]]] | None,
) -> Dict[str, Dict[str, Rule | Dict[str, Any]]]:
    """
    Filter rules by id.

    If rule_configs is None, no rules are returned.
    """
    if rule_configs is None:
        return dict()

    enabled_set: Dict[str, Dict[str, Dict[str, Any] | Rule]] = dict()
    for rule_id in rule_configs.keys():
        if rule_id not in rules:
            raise ValueError(f"Unknown rule id: {rule_id}")
        if rule_id not in enabled_set:
            enabled_set[rule_id] = dict()
        rule_config = rule_configs[rule_id]
        enabled_set[rule_id]["rule"] = rules[rule_id]
        enabled_set[rule_id]["config"] = rule_config

    return enabled_set


def run_linter(
    document: Document,
    rule_configs: Dict[str, Dict[str, Dict[str, Any]]] | None = None
) -> List[RuleResult]:
    """
    Run lint rules against a document and return normalized results.

    - document: the parsed Document to lint.
    - rule_configs: mapping of rule_id to configuration dictionary

    Note: Rules without an entry are disabled.
    """
    all_rules = discover_rules()
    active_rules = _select_rules(all_rules, rule_configs)

    all_results: List[RuleResult] = []
    for rule_id in active_rules.keys():
        rule_config = active_rules[rule_id]["config"]
        if not isinstance(rule_config, dict):
            raise ValueError(
                f"Invalid configuration for rule {rule_id}: {rule_config}"
            )

        rule = active_rules[rule_id]["rule"]
        if not isinstance(rule, Rule):
            raise ValueError(
                f"Invalid rule object for {rule_id}: {rule}"
            )

        raw_results = rule.func(document, rule_config)
        for res in raw_results:
            normalized = replace(res, rule_id=rule_id)
            all_results.append(normalized)

    return all_results
