from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class TableHeaderSpec:
    match: str  # "exact" or "superset"
    columns: List[str]


@dataclass
class TableRowsSpec:
    min: Optional[int] = None
    max: Optional[int] = None


@dataclass
class TableSpec:
    id: str
    required: bool = True
    repeatable: bool = False
    header: Optional[TableHeaderSpec] = None
    rows: Optional[TableRowsSpec] = None


@dataclass
class SectionSpec:
    id: str
    level: int
    required: bool = True
    repeatable: bool = False

    title: Optional[str] = None
    title_pattern: Optional[str] = None

    children: List["SectionSpec"] = field(default_factory=list)
    tables: List[TableSpec] = field(default_factory=list)


@dataclass
class MarkdownSchema:
    sections: List[SectionSpec]


def load_markdown_schema(cfg: Dict[str, Any]) -> MarkdownSchema:
    """
    Load a MarkdownSchema from a parsed YAML config.

    Expected top level shape:

      markdown:
        sections:
          - id: ...
            title: ...
            level: 2
            required: true
            repeatable: false
            children: [...]
            tables: [...]

    This loader is intentionally strict about required keys so that
    schema mistakes are caught early.
    """
    md_cfg = cfg.get("markdown")
    if md_cfg is None:
        raise ValueError("Missing 'markdown' key at top level of schema "
                         "config")

    sections_cfg = md_cfg.get("sections")
    if not isinstance(sections_cfg, list):
        raise ValueError("'markdown.sections' must be a list")

    sections = [_load_section_spec(s) for s in sections_cfg]

    return MarkdownSchema(sections=sections)


def _load_section_spec(data: Dict[str, Any]) -> SectionSpec:
    if not isinstance(data, dict):
        raise ValueError(f"Section spec must be a mapping, got: {type(data)}")

    sec_id = data.get("id")
    level = data.get("level")
    title = data.get("title")
    title_pattern = data.get("title_pattern")
    required = data.get("required", True)
    repeatable = data.get("repeatable", False)

    if sec_id is None:
        raise ValueError("Section spec is missing required 'id' field")
    if level is None:
        raise ValueError(f"Section '{sec_id}' is missing required 'level' "
                         "field")
    if title is None and title_pattern is None:
        raise ValueError(
            f"Section '{sec_id}' must define either 'title' or "
            "'title_pattern'"
        )

    # Children
    children_cfg = data.get("children", [])
    if children_cfg is None:
        children_cfg = []
    if not isinstance(children_cfg, list):
        raise ValueError(f"Section '{sec_id}': 'children' must be a list "
                         "if present")

    children = [_load_section_spec(c) for c in children_cfg]

    # Tables
    tables_cfg = data.get("tables", [])
    if tables_cfg is None:
        tables_cfg = []
    if not isinstance(tables_cfg, list):
        raise ValueError(f"Section '{sec_id}': 'tables' must be a list if "
                         "present")

    tables = [_load_table_spec(t, sec_id) for t in tables_cfg]

    return SectionSpec(
        id=sec_id,
        level=int(level),
        required=bool(required),
        repeatable=bool(repeatable),
        title=title,
        title_pattern=title_pattern,
        children=children,
        tables=tables,
    )


def _load_table_spec(
        data: Dict[str, Any], parent_section_id: str
        ) -> TableSpec:
    if not isinstance(data, dict):
        raise ValueError(
            f"Table spec under section '{parent_section_id}' must be a "
            "mapping, "
            f"got: {type(data)}"
        )

    table_id = data.get("id")
    if table_id is None:
        raise ValueError(
            f"Table spec under section '{parent_section_id}' is missing 'id'"
        )

    required = bool(data.get("required", True))
    repeatable = bool(data.get("repeatable", False))

    header_spec = None
    header_cfg = data.get("header")
    if header_cfg is not None:
        if not isinstance(header_cfg, dict):
            raise ValueError(
                f"Table '{table_id}': 'header' must be a mapping if present"
            )
        match_mode = header_cfg.get("match", "exact")
        if match_mode not in ("exact", "superset"):
            raise ValueError(
                f"Table '{table_id}': header.match must be 'exact' or "
                "'superset'"
            )
        columns = header_cfg.get("columns")
        if not isinstance(columns, list) or not all(
            isinstance(c, str) for c in columns
        ):
            raise ValueError(
                f"Table '{table_id}': header.columns must be a list of "
                "strings"
            )
        header_spec = TableHeaderSpec(match=match_mode, columns=columns)

    rows_spec = None
    rows_cfg = data.get("rows")
    if rows_cfg is not None:
        if not isinstance(rows_cfg, dict):
            raise ValueError(
                f"Table '{table_id}': 'rows' must be a mapping if present"
            )
        min_rows = rows_cfg.get("min")
        max_rows = rows_cfg.get("max")
        # Allow null to mean "no bound"
        if min_rows is not None:
            min_rows = int(min_rows)
        if max_rows is not None:
            max_rows = int(max_rows)
        rows_spec = TableRowsSpec(min=min_rows, max=max_rows)

    return TableSpec(
        id=table_id,
        required=required,
        repeatable=repeatable,
        header=header_spec,
        rows=rows_spec,
    )
