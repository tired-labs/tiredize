from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document
from typing import Any
from typing import Dict
from typing import List


def validate_hidden(
    document: Document,
    config: Dict[str, Any],
) -> List[RuleResult]:
    """Should not be discovered because the module is private."""
    return []
