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


_TOP_LEVEL_KEYS = {'allow_extra_sections', 'enforce_order', 'sections'}
_SECTION_KEYS = {'level', 'name', 'pattern', 'repeat', 'required', 'sections'}


def load_schema(yaml_string: str) -> SchemaConfig:
    raw = yaml.safe_load(yaml_string)
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"Schema must be a YAML mapping, got {type(raw).__name__}."
        )
    unknown = set(raw.keys()) - _TOP_LEVEL_KEYS
    if unknown:
        raise ValueError(
            f"Unknown top-level key(s): {', '.join(sorted(unknown))}."
        )
    raw_sections = raw.get('sections', [])
    if not isinstance(raw_sections, list):
        raise ValueError(
            "'sections' must be a list."
        )
    allow_extra = raw.get('allow_extra_sections', False)
    if not isinstance(allow_extra, bool):
        raise ValueError(
            f"'allow_extra_sections' must be a bool, "
            f"got {type(allow_extra).__name__}."
        )
    enforce = raw.get('enforce_order', True)
    if not isinstance(enforce, bool):
        raise ValueError(
            f"'enforce_order' must be a bool, "
            f"got {type(enforce).__name__}."
        )
    return SchemaConfig(
        allow_extra_sections=allow_extra,
        enforce_order=enforce,
        sections=[
            _load_section(s, parent_level=0)
            for s in raw_sections
        ],
    )


def _load_section(raw: dict, parent_level: int) -> SchemaSection:
    if not isinstance(raw, dict):
        raise ValueError(
            f"Each section must be a YAML mapping, "
            f"got {type(raw).__name__}."
        )
    unknown = set(raw.keys()) - _SECTION_KEYS
    if unknown:
        raise ValueError(
            f"Unknown section key(s): {', '.join(sorted(unknown))}."
        )
    name = raw.get('name')
    if name is not None and not isinstance(name, str):
        raise ValueError(
            f"'name' must be a string, "
            f"got {type(name).__name__}."
        )
    pattern = raw.get('pattern')
    if pattern is not None and not isinstance(pattern, str):
        raise ValueError(
            f"'pattern' must be a string, "
            f"got {type(pattern).__name__}."
        )

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
    if not isinstance(level, int) or isinstance(level, bool):
        raise ValueError(
            f"'level' must be an integer, "
            f"got {type(level).__name__}."
        )
    if level < 1 or level > 6:
        raise ValueError(
            f"Section level {level} must be between 1 and 6."
        )
    if level <= parent_level:
        raise ValueError(
            f"Section level {level} must be greater than "
            f"parent level {parent_level}."
        )

    repeat_min = None
    repeat_max = None
    repeat = raw.get('repeat')
    if repeat is None:
        pass
    elif repeat is True:
        repeat_min = 1
    elif isinstance(repeat, dict):
        unknown_repeat = set(repeat.keys()) - {'min', 'max'}
        if unknown_repeat:
            raise ValueError(
                f"Unknown repeat key(s): "
                f"{', '.join(sorted(unknown_repeat))}."
            )
        repeat_min = repeat.get('min', 1)
        repeat_max = repeat.get('max')
    else:
        raise ValueError(
            f"'repeat' must be true or a mapping with "
            f"min/max bounds (e.g., repeat: {{min: 1, max: 3}}), "
            f"got {type(repeat).__name__}: {repeat!r}."
        )

    if repeat_min is not None and (
            not isinstance(repeat_min, int)
            or isinstance(repeat_min, bool)):
        raise ValueError("repeat.min must be an integer.")
    if repeat_max is not None and (
            not isinstance(repeat_max, int)
            or isinstance(repeat_max, bool)):
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

    raw_sections = raw.get('sections', [])
    if not isinstance(raw_sections, list):
        raise ValueError(
            "'sections' must be a list."
        )
    required = raw.get('required', True)
    if not isinstance(required, bool):
        raise ValueError(
            f"'required' must be a bool, "
            f"got {type(required).__name__}."
        )
    return SchemaSection(
        level=level,
        name=name,
        pattern=pattern,
        repeat_max=repeat_max,
        repeat_min=repeat_min,
        required=required,
        sections=[
            _load_section(s, parent_level=level)
            for s in raw_sections
        ],
    )
