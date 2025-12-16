from __future__ import annotations
from dataclasses import dataclass
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document
from typing import Any, Callable, Dict, List
import importlib
import inspect
import pkgutil


RuleFunc = Callable[[Document, Dict[str, Any]], List[RuleResult]]


@dataclass(frozen=True)
class Rule:
    """
    Class containing a single lint rule.
    """
    id: str
    func: RuleFunc
    description: str | None = None


def _iter_rule_modules(package_name: str) -> List[str]:
    """
    Return fully qualified module names for all rule modules.

    A rule module is any non private Python module directly under this package.
    """
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        # Not a package, nothing to iterate
        return []

    module_names: List[str] = []

    prefix = package.__name__ + "."
    for _, name, ispkg in pkgutil.iter_modules(package.__path__, prefix):
        # Skip subpackages for now, only plain modules
        if ispkg:
            continue

        short_name = name.rsplit(".", 1)[-1]
        if short_name.startswith("_"):
            continue

        module_names.append(name)

    return module_names


def _is_rule_function(name: str, obj: Any) -> bool:
    """
    A rule is any callable named 'validate'.
    """
    return callable(obj) and name == "validate"


def _rule_id(module_name: str, func_name: str) -> str:
    """
    Compute the rule id from module and function names.

    Example:
        module_name = 'tiredize.linter.rules.whitespace'
        func_name = 'validate_newline_at_eof'
        result = 'whitespace.validate_newline_at_eof'
    """
    short_module = module_name.rsplit(".", 1)[-1]
    return f"{short_module}"


def discover_rules(package: str | None = None) -> Dict[str, Rule]:
    """
    Import all rule modules and return a mapping of rule_id to definitions.

    If package is None, rules are discovered under tiredize.linter.rules.
    If package is provided, it must be the dotted name of a Python package
    that contains rule modules.
    """
    package_name = package or __name__
    rules: Dict[str, Rule] = {}

    module_names: List[str] = _iter_rule_modules(package_name)
    for module_name in module_names:
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module):
            if not _is_rule_function(name, obj):
                continue

            func: RuleFunc = obj
            rule_id = _rule_id(module_name, name)
            description = inspect.getdoc(func)
            if description:
                description = description.strip()

            rules[rule_id] = Rule(
                id=rule_id,
                func=func,
                description=description,
            )

    return rules
