# Standard library
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field


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
    enforce_order: bool = True
    allow_extra_sections: bool = False
    sections: list[SchemaSection] = field(default_factory=list)
