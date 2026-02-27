# Standard library
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field

# Third-party
import yaml


@dataclass(frozen=True)
class SchemaSection:
    name: str | None = None
    pattern: str | None = None
    level: int = 1
    required: bool = True
    repeat_min: int | None = None
    repeat_max: int | None = None
    sections: list[SchemaSection] = field(default_factory=list)


@dataclass(frozen=True)
class SchemaConfig:
    allow_extra_sections: bool = False
    enforce_order: bool = True
    sections: list[SchemaSection] = field(default_factory=list)


def load_schema(yaml_string: str) -> SchemaConfig:
    raw = yaml.safe_load(yaml_string)
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
