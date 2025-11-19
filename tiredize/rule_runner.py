from tiredize.document import Document
from tiredize.types import RuleResult
from tiredize.validators.front_matter import validate_front_matter
from tiredize.validators.line_length import validate_line_length
from tiredize.validators.whitespace import validate_whitespace
from typing import Dict, List, Callable


# Registry maps rule names to validator functions
# Each validator: (Document, schema_dict) -> List[RuleResult]
RULE_REGISTRY: Dict[str, Callable[[Document, Dict], List[RuleResult]]] = {
    "line_length": validate_line_length,
    "whitespace": validate_whitespace,
    "front_matter": validate_front_matter
}


def run_rules(doc: Document, schema: Dict) -> List[RuleResult]:
    """
    Execute all validators defined in the RULE_REGISTRY.

    The schema may enable or disable specific rules via:
      rules:
        line_length: true
        sections: false
        ...

    For now, if no explicit toggle is present, the rule runs by default.
    """
    rule_cfg = schema.get("rules", {})

    results: List[RuleResult] = []

    for rule_name, validator in RULE_REGISTRY.items():
        enabled = rule_cfg.get(rule_name, True)
        if not enabled:
            continue

        rule_results = validator(doc, schema)
        results.extend(rule_results)

    return results
