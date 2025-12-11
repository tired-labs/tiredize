from tiredize.markdown.types.document import Document
from tiredize.types import RuleResult
from tiredize.validators.line_length import validate_line_length
from tiredize.validators.whitespace import validate_whitespace
from typing import Callable, Dict, Any, List


RuleFunc = Callable[[Document, Dict[str, Any]], List[RuleResult]]
RULES: Dict[str, RuleFunc] = {}

RULES["line_length"] = validate_line_length
RULES["whitespace"] = validate_whitespace
