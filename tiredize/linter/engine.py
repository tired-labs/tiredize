# Standard library
from __future__ import annotations
from dataclasses import replace
from typing import Any

# Local
from tiredize.core_types import RuleNotFoundError
from tiredize.core_types import RuleResult
from tiredize.linter.rules import Rule
from tiredize.linter.rules import discover_rules
from tiredize.markdown.types.document import Document


def _select_rules(
    rules: dict[str, Rule],
    rule_configs: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Rule | dict[str, Any]]]:
    """
    Filter rules by id.

    If rule_configs is None, no rules are returned.
    """
    if rule_configs is None:
        return dict()

    enabled_set: dict[str, dict[str, dict[str, Any] | Rule]] = dict()
    for rule_id in rule_configs.keys():
        if rule_id not in rules:
            raise RuleNotFoundError(f"Unknown rule id: {rule_id}")
        if rule_id not in enabled_set:
            enabled_set[rule_id] = dict()
        rule_config = rule_configs[rule_id]
        enabled_set[rule_id]["rule"] = rules[rule_id]
        enabled_set[rule_id]["config"] = rule_config

    return enabled_set


def run_linter(
    document: Document,
    rule_configs: dict[str, dict[str, Any]] | None = None
) -> list[RuleResult]:
    """
    Run lint rules against a document and return normalized results.

    - document: the parsed Document to lint.
    - rule_configs: mapping of rule_id to configuration dictionary

    Note: Rules without an entry are disabled.
    """
    all_rules = discover_rules()
    active_rules = _select_rules(all_rules, rule_configs)

    all_results: list[RuleResult] = []
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
