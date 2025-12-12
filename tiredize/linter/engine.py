# tiredize/linter/engine.py

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, List

from tiredize.markdown.types.document import Document
from tiredize.linter.rules import Rule, discover_rules
from tiredize.linter.types import RuleResult


def _select_rules(
    all_rules: Dict[str, Rule],
    rules_config: Dict[str, Dict[str, Dict[str, Any]]] | None,
) -> Dict[str, Dict[str, Rule | Dict[str, Any]]]:
    """
    Filter rules by id.

    If rules_config is None, no rules are returned.
    """
    if rules_config is None:
        return dict()

    enabled_set: Dict[str, Dict[str, Dict[str, Any] | Rule]] = dict()
    for module_name in rules_config.keys():
        module_dict = rules_config[module_name]
        for rule_name in rules_config[module_name].keys():
            rule_config = module_dict[rule_name]
            rule_id = f"{module_name}.{rule_name}"
            if rule_id not in enabled_set:
                enabled_set[rule_id] = dict()
            if rule_id not in all_rules:
                raise ValueError(f"Unknown rule id: {rule_id}")
            enabled_set[rule_id]["rule"] = all_rules[rule_id]
            enabled_set[rule_id]["config"] = dict()
            enabled_set[rule_id]["config"][rule_name] = rule_config

    return enabled_set


def run_linter(
    document: Document,
    rules_config: Dict[str, Dict[str, Dict[str, Any]]] | None = None
) -> List[RuleResult]:
    """
    Run lint rules against a document and return normalized results.

    - document: the parsed Document to lint.
    - rule_configs: mapping of rule_id to config dict, for example:
        {
            "whitespace":
                "max_line_length": 120
        }

    Rules without an entry are disabled.
    """
    discovered = discover_rules()
    active_rules = _select_rules(discovered, rules_config)

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
            # Always normalize rule_id to the canonical id from discovery.
            normalized = replace(res, rule_id=rule_id)
            all_results.append(normalized)

    return all_results
