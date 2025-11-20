from jsonschema import Draft202012Validator
from tiredize.document import Document
from tiredize.types import RuleResult
from typing import Dict, List, Any


def validate_front_matter(
        doc: Document, schema: Dict[str, Any]
        ) -> List[RuleResult]:
    """
    Validate document.front_matter using a JSON Schema (Draft 2020-12).

    Expected config shape in `schema`:

      front_matter:
        schema: <dict loaded from JSON Schema YAML/JSON>

    The CLI or caller is responsible for loading the JSON Schema file and
    placing the parsed schema dict under front_matter.schema.
    """
    cfg = schema.get("front_matter", {})
    fm_schema = cfg.get("schema")

    # If no schema is configured, this rule is a no-op.
    if not fm_schema:
        return []

    validator = Draft202012Validator(fm_schema)

    results: List[RuleResult] = []

    # Use iter_errors to collect all violations, not just the first.
    for err in validator.iter_errors(doc.front_matter):
        # Build a path string like "procedures[0].id"
        if err.path:
            segments = []
            for p in err.path:
                if isinstance(p, int):
                    segments[-1] = f"{segments[-1]}[{p}]"
                else:
                    segments.append(str(p))
            path = ".".join(segments)
        else:
            path = "<root>"

        message = f"{path}: {err.message}"

        results.append(
            RuleResult(
                rule_id="front_matter_schema",
                line=0,  # front matter line tracking can be added later
                message=message,
            )
        )

    return results
