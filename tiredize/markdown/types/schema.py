# Standard library
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
import re

# Third-party
import yaml


@dataclass(frozen=True)
class SchemaSection:
    level: int = 1
    name: str | None = None
    pattern: str | None = None
    repeat_max: int | None = None
    repeat_min: int | None = None
    required: bool = True
    sections: list[SchemaSection] = field(default_factory=list)


@dataclass(frozen=True)
class SchemaConfig:
    allow_extra_sections: bool = False
    enforce_order: bool = True
    sections: list[SchemaSection] = field(default_factory=list)


def load_schema(yaml_string: str) -> SchemaConfig:
    raw = yaml.safe_load(yaml_string)
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"Schema must be a YAML mapping, got {type(raw).__name__}."
        )
    return SchemaConfig(
        allow_extra_sections=raw.get('allow_extra_sections', False),
        enforce_order=raw.get('enforce_order', True),
        sections=[
            _load_section(s, parent_level=0)
            for s in raw.get('sections', [])
        ],
    )


def _load_section(raw: dict, parent_level: int) -> SchemaSection:
    name = raw.get('name')
    pattern = raw.get('pattern')

    if name is not None and pattern is not None:
        raise ValueError(
            "Section must have 'name' or 'pattern', not both."
        )
    if name is None and pattern is None:
        raise ValueError(
            "Section must have either 'name' or 'pattern'."
        )

    if pattern is not None:
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(
                f"Invalid regex pattern '{pattern}': {exc}"
            ) from exc

    expected_level = parent_level + 1
    level = raw.get('level', expected_level)
    if level <= parent_level:
        raise ValueError(
            f"Section level {level} must be greater than "
            f"parent level {parent_level}."
        )

    repeat_min = None
    repeat_max = None
    repeat = raw.get('repeat')
    if repeat is True:
        repeat_min = 1
    elif isinstance(repeat, dict):
        repeat_min = repeat.get('min', 1)
        repeat_max = repeat.get('max')

    if repeat_min is not None and not isinstance(repeat_min, int):
        raise ValueError("repeat.min must be an integer.")
    if repeat_max is not None and not isinstance(repeat_max, int):
        raise ValueError("repeat.max must be an integer.")
    if repeat_min is not None and repeat_min < 0:
        raise ValueError("repeat.min must not be negative.")
    if repeat_max is not None and repeat_max < 0:
        raise ValueError("repeat.max must not be negative.")
    if (repeat_min is not None and repeat_max is not None
            and repeat_max < repeat_min):
        raise ValueError(
            f"repeat.max ({repeat_max}) must not be less than "
            f"repeat.min ({repeat_min})."
        )

    return SchemaSection(
        level=level,
        name=name,
        pattern=pattern,
        repeat_max=repeat_max,
        repeat_min=repeat_min,
        required=raw.get('required', True),
        sections=[
            _load_section(s, parent_level=level)
            for s in raw.get('sections', [])
        ],
    )
