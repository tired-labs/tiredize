# Standard library
from __future__ import annotations
import datetime
from dataclasses import dataclass
from dataclasses import field

# Third-party
import yaml

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document


# ============================================================
# Duplicate-key-detecting YAML loader
# ============================================================


class _DuplicateKeyLoader(yaml.SafeLoader):
    """SafeLoader subclass that raises on duplicate mapping keys."""
    pass


def _construct_no_duplicates(loader, node):
    pairs = loader.construct_pairs(node)
    seen = {}
    for key, _ in pairs:
        if key in seen:
            raise ValueError(
                f"Frontmatter contains duplicate key: '{key}'"
            )
        seen[key] = True
    return dict(pairs)


_DuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_no_duplicates,
)


def safe_load_yaml(text: str):
    """Load YAML with duplicate key detection."""
    return yaml.load(text, Loader=_DuplicateKeyLoader)


# ============================================================
# Schema data model
# ============================================================


_VALID_TYPES = frozenset({
    "string", "int", "float", "bool", "date", "list",
})

_TYPE_MAP = {
    "string": str,
    "int": int,
    "float": float,
    "bool": bool,
    "date": datetime.date,
    "list": list,
}

_TOP_LEVEL_KEYS = frozenset({"allow_extra_fields", "fields"})
_FIELD_KEYS = frozenset({"type", "required", "allowed"})


@dataclass(frozen=True)
class FieldSchema:
    type: str
    required: bool = True
    allowed: list | None = None


@dataclass(frozen=True)
class FrontmatterSchema:
    allow_extra_fields: bool = False
    fields: dict[str, FieldSchema] = field(default_factory=dict)


# ============================================================
# Schema loader
# ============================================================


def load_frontmatter_schema(yaml_string: str) -> FrontmatterSchema:
    """Parse and validate a frontmatter schema YAML string."""
    raw = yaml.safe_load(yaml_string)
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"Schema must be a YAML mapping, "
            f"got {type(raw).__name__}."
        )

    unknown = set(raw.keys()) - _TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(
            f"Unknown top-level key(s): "
            f"{', '.join(sorted(unknown))}."
        )

    if "fields" not in raw:
        raise ValueError("Schema must contain a 'fields' key.")

    raw_fields = raw["fields"]
    if not isinstance(raw_fields, dict):
        raise ValueError(
            f"'fields' must be a YAML mapping, "
            f"got {type(raw_fields).__name__}."
        )

    allow_extra = raw.get("allow_extra_fields", False)
    if not isinstance(allow_extra, bool):
        raise ValueError(
            f"'allow_extra_fields' must be a bool, "
            f"got {type(allow_extra).__name__}."
        )

    fields = {}
    for name, definition in raw_fields.items():
        fields[name] = _load_field(name, definition)

    return FrontmatterSchema(
        allow_extra_fields=allow_extra,
        fields=fields,
    )


def _load_field(name: str, raw: dict) -> FieldSchema:
    """Validate and load a single field definition."""
    if not isinstance(raw, dict):
        raise ValueError(
            f"Field '{name}' definition must be a YAML mapping, "
            f"got {type(raw).__name__}."
        )

    unknown = set(raw.keys()) - _FIELD_KEYS
    if unknown:
        raise ValueError(
            f"Unknown property in field '{name}': "
            f"{', '.join(sorted(unknown))}."
        )

    if "type" not in raw:
        raise ValueError(
            f"Field '{name}' must declare a 'type'."
        )

    field_type = raw["type"]
    if not isinstance(field_type, str) or field_type not in _VALID_TYPES:
        raise ValueError(
            f"Field '{name}' has unknown type '{field_type}'. "
            f"Valid types: {', '.join(sorted(_VALID_TYPES))}."
        )

    required = raw.get("required", True)
    if not isinstance(required, bool):
        raise ValueError(
            f"'required' for field '{name}' must be a bool, "
            f"got {type(required).__name__}."
        )

    allowed = raw.get("allowed")
    if allowed is not None:
        if not isinstance(allowed, list):
            raise ValueError(
                f"'allowed' for field '{name}' must be a list, "
                f"got {type(allowed).__name__}."
            )
        if len(allowed) == 0:
            raise ValueError(
                f"'allowed' for field '{name}' must not be empty."
            )
        _validate_allowed_types(name, field_type, allowed)

    return FieldSchema(
        type=field_type,
        required=required,
        allowed=allowed,
    )


def _validate_allowed_types(
    name: str,
    field_type: str,
    allowed: list,
) -> None:
    """Validate that allowed values match the declared field type."""
    if field_type == "list":
        # For list fields, allowed values must be strings
        for value in allowed:
            if not isinstance(value, str):
                raise ValueError(
                    f"'allowed' values for list field '{name}' "
                    f"must be strings, got {type(value).__name__}: "
                    f"{value!r}."
                )
    else:
        expected_python_type = _TYPE_MAP[field_type]
        for value in allowed:
            # bool-is-int guard
            if expected_python_type is int and isinstance(value, bool):
                raise ValueError(
                    f"'allowed' value {value!r} for field '{name}' "
                    f"has wrong type (bool, expected {field_type})."
                )
            if not isinstance(value, expected_python_type):
                raise ValueError(
                    f"'allowed' value {value!r} for field '{name}' "
                    f"has wrong type "
                    f"({type(value).__name__}, expected {field_type})."
                )


# ============================================================
# Validator
# ============================================================


def validate(
    document: Document,
    schema: FrontmatterSchema,
) -> list[RuleResult]:
    """Validate document frontmatter against a schema."""
    results: list[RuleResult] = []

    fm = document.frontmatter
    if fm is not None:
        pos = fm.position
    else:
        pos = Position(offset=0, length=0)

    # Re-parse frontmatter with duplicate key detection
    if fm is not None and fm.string:
        # Extract the YAML content between the --- delimiters.
        # fm.string is "---\n<yaml>\n---\n", so strip the
        # opening "---\n" and closing "\n---\n".
        raw_text = fm.string
        start = raw_text.index("\n") + 1
        end = raw_text.rindex("\n---\n")
        yaml_content = raw_text[start:end]
        if yaml_content.strip():
            try:
                safe_load_yaml(yaml_content)
            except ValueError as exc:
                results.append(RuleResult(
                    message=str(exc),
                    position=pos,
                    rule_id="schema.frontmatter.duplicate_key",
                ))
                # Stop validation on duplicate keys — data is
                # unreliable
                return results

    content = fm.content if fm is not None else {}
    if content is None:
        content = {}

    # Check for missing required fields
    for name, field_schema in schema.fields.items():
        if name not in content and field_schema.required:
            results.append(RuleResult(
                message=f"Missing required field: '{name}'",
                position=pos,
                rule_id="schema.frontmatter.missing_field",
            ))

    # Check for extra fields
    if not schema.allow_extra_fields:
        for key in content:
            if key not in schema.fields:
                results.append(RuleResult(
                    message=f"Unexpected field: '{key}'",
                    position=pos,
                    rule_id="schema.frontmatter.extra_field",
                ))

    # Validate each present field
    for name, field_schema in schema.fields.items():
        if name not in content:
            continue

        value = content[name]

        # Map check (before type check)
        if isinstance(value, dict):
            results.append(RuleResult(
                message=(
                    f"Field '{name}' is a map — "
                    f"maps are not supported"
                ),
                position=pos,
                rule_id="schema.frontmatter.map_not_supported",
            ))
            continue

        # Type check
        expected_type = _TYPE_MAP[field_schema.type]
        type_ok = True

        if expected_type is int:
            # Reject bool for int fields
            if isinstance(value, bool) or not isinstance(value, int):
                type_ok = False
        elif not isinstance(value, expected_type):
            type_ok = False

        if not type_ok:
            actual_type = type(value).__name__
            results.append(RuleResult(
                message=(
                    f"Field '{name}' has wrong type: "
                    f"expected {field_schema.type}, "
                    f"got {actual_type}"
                ),
                position=pos,
                rule_id="schema.frontmatter.wrong_type",
            ))
            continue

        # List-specific checks
        if field_schema.type == "list":
            _validate_list_field(
                name, value, field_schema, pos, results
            )
        else:
            # Scalar allowed check
            if (field_schema.allowed is not None
                    and value not in field_schema.allowed):
                results.append(RuleResult(
                    message=(
                        f"Field '{name}' value '{value}' "
                        f"is not allowed. "
                        f"Accepted values: "
                        f"{field_schema.allowed}"
                    ),
                    position=pos,
                    rule_id=(
                        "schema.frontmatter.value_not_allowed"
                    ),
                ))

    return results


def _validate_list_field(
    name: str,
    value: list,
    field_schema: FieldSchema,
    pos: Position,
    results: list[RuleResult],
) -> None:
    """Validate a list field's items."""
    # Check all items are strings
    has_non_string = False
    for item in value:
        if not isinstance(item, str):
            has_non_string = True
            results.append(RuleResult(
                message=(
                    f"List field '{name}' contains "
                    f"non-string item: {item!r} "
                    f"({type(item).__name__})"
                ),
                position=pos,
                rule_id=(
                    "schema.frontmatter.list_item_not_string"
                ),
            ))

    if has_non_string:
        return

    # Check for duplicates
    seen = set()
    for item in value:
        if item in seen:
            results.append(RuleResult(
                message=(
                    f"List field '{name}' contains "
                    f"duplicate item: '{item}'"
                ),
                position=pos,
                rule_id=(
                    "schema.frontmatter.duplicate_list_item"
                ),
            ))
        seen.add(item)

    # Check allowed values
    if field_schema.allowed is not None:
        for item in value:
            if item not in field_schema.allowed:
                results.append(RuleResult(
                    message=(
                        f"List field '{name}' contains "
                        f"disallowed item: '{item}'. "
                        f"Accepted values: "
                        f"{field_schema.allowed}"
                    ),
                    position=pos,
                    rule_id=(
                        "schema.frontmatter.value_not_allowed"
                    ),
                ))
