# tiredize/validators/markdown_structure.py

from __future__ import annotations

import re
from typing import Dict, List, Any, Tuple, Optional

from tiredize.document import Document, Heading, Table
from tiredize.types import RuleResult
from tiredize.markdown_schema import (
    load_markdown_schema,
    MarkdownSchema,
    SectionSpec,
    TableSpec,
    TableHeaderSpec,
    TableRowsSpec,
)


def validate_markdown_structure(
        doc: Document, schema_cfg: Dict[str, Any]
        ) -> List[RuleResult]:
    """
    Validate the markdown body against the configured structural schema.

    Enforces:
      - Required sections (by title or title_pattern) at specific heading
        levels
      - Required child sections under a parent section
      - Required tables under sections
      - Table header matching for tables attached to sections
    """
    results: List[RuleResult] = []

    # If no markdown schema is configured, this rule is a no-op.
    if "markdown" not in schema_cfg:
        return results

    md_schema: MarkdownSchema = load_markdown_schema(schema_cfg)

    # Treat the whole document as the parent span for top-level sections.
    parent_span = (0, _doc_end_line(doc))

    for sec_spec in md_schema.sections:
        sec_results = _validate_section_spec(
            doc=doc,
            spec=sec_spec,
            parent_span=parent_span,
        )
        results.extend(sec_results)

    return results


def _doc_end_line(doc: Document) -> int:
    """Return one-past-the-last line number of the document body."""
    return len(doc.body.splitlines()) + 1


def _match_heading_title(spec: SectionSpec, heading: Heading) -> bool:
    if spec.title is not None:
        return heading.title == spec.title
    if spec.title_pattern is not None:
        return re.match(spec.title_pattern, heading.title) is not None
    return False


def _find_matching_headings(
    doc: Document,
    spec: SectionSpec,
    parent_span: Tuple[int, int],
) -> List[Tuple[int, Heading]]:
    """
    Find headings that match this section spec within the given parent span.

    Returns list of (index_in_doc_headings, Heading).
    """
    start_line, end_line = parent_span
    matches: List[Tuple[int, Heading]] = []

    for idx, h in enumerate(doc.headings):
        if h.line <= start_line:
            continue
        if h.line >= end_line:
            break
        if h.level != spec.level:
            continue
        if not _match_heading_title(spec, h):
            continue
        matches.append((idx, h))

    return matches


def _find_section_span(
    doc: Document,
    heading_index: int,
    level: int,
    parent_span: Tuple[int, int],
) -> Tuple[int, int]:
    """
    Given the index of a heading in doc.headings and its level, compute the
    span of this section as (start_line_exclusive, end_line_exclusive).

    The span is bounded by:
      - the next heading at level <= this level inside the parent span, or
      - the parent span end if no such heading exists.
    """
    start_line = doc.headings[heading_index].line
    parent_start, parent_end = parent_span

    end_line = parent_end
    for j in range(heading_index + 1, len(doc.headings)):
        h = doc.headings[j]
        if h.line >= parent_end:
            break
        if h.level <= level:
            end_line = h.line
            break

    return (start_line, end_line)


def _validate_section_spec(
    doc: Document,
    spec: SectionSpec,
    parent_span: Tuple[int, int],
) -> List[RuleResult]:
    results: List[RuleResult] = []

    matches = _find_matching_headings(doc, spec, parent_span)

    # Required section missing entirely
    if not matches and spec.required:
        results.append(
            RuleResult(
                rule_id="md_section_missing",
                line=0,
                message=f"Required section '{spec.id}' (level {spec.level}) "
                "not found",
            )
        )
        # If the section is missing, we do not descend into children or tables.
        return results

    # Multiple occurrences where at most one is allowed
    if not spec.repeatable and len(matches) > 1:
        results.append(
            RuleResult(
                rule_id="md_section_multiple",
                line=matches[1][1].line,
                message=f"Section '{spec.id}' appears more than once",
            )
        )

    # For each matched section heading, validate its tables and children
    for idx, heading in matches:
        section_span = _find_section_span(
            doc=doc,
            heading_index=idx,
            level=spec.level,
            parent_span=parent_span,
        )

        # Validate tables anchored to this section
        results.extend(
            _validate_tables_in_section(
                doc=doc,
                spec=spec,
                section_span=section_span,
            )
        )

        # Validate child sections inside this section span
        for child_spec in spec.children:
            results.extend(
                _validate_section_spec(
                    doc=doc,
                    spec=child_spec,
                    parent_span=section_span,
                )
            )

    return results


def _tables_in_span(doc: Document, span: Tuple[int, int]) -> List[Table]:
    start_line, end_line = span
    return [
        t
        for t in doc.tables
        if t.start_line > start_line and t.start_line < end_line
    ]


def _validate_table_header(
    table: Table,
    t_spec: TableSpec,
    parent_section_id: str,
) -> Optional[RuleResult]:
    header_spec: Optional[TableHeaderSpec] = t_spec.header
    if header_spec is None:
        return None

    expected = header_spec.columns
    actual = table.header

    if header_spec.match == "exact":
        if actual != expected:
            return RuleResult(
                rule_id="md_table_header",
                line=table.start_line,
                message=(
                    f"Table '{t_spec.id}' in section '{parent_section_id}' "
                    f"has header {actual}, expected {expected}"
                ),
            )
        return None

    if header_spec.match == "superset":
        # actual must contain expected columns in order
        try:
            idx = 0
            for col in expected:
                idx = actual.index(col, idx) + 1
        except ValueError:
            return RuleResult(
                rule_id="md_table_header",
                line=table.start_line,
                message=(
                    f"Table '{t_spec.id}' in section '{parent_section_id}' "
                    f"does not contain expected header columns {expected}"
                ),
            )
        return None

    # Unknown match mode; treat as configuration error
    return RuleResult(
        rule_id="md_table_header",
        line=table.start_line,
        message=(
            f"Unsupported header.match mode '{header_spec.match}' "
            f"for table '{t_spec.id}'"
        ),
    )


def _validate_tables_in_section(
    doc: Document,
    spec: SectionSpec,
    section_span: Tuple[int, int],
) -> List[RuleResult]:
    results: List[RuleResult] = []

    if not spec.tables:
        return results

    tables_in_section = _tables_in_span(doc, section_span)

    for t_spec in spec.tables:
        if tables_in_section:
            table: Optional[Table] = tables_in_section[0]
        else:
            table: Optional[Table] = None

        if table is None:
            if t_spec.required:
                results.append(
                    RuleResult(
                        rule_id="md_table_missing",
                        line=section_span[0],
                        message=(
                            f"Required table '{t_spec.id}' "
                            f"not found in section '{spec.id}'"
                        ),
                    )
                )
            continue

        # Header validation
        if t_spec.header is not None:
            header_result = _validate_table_header(
                table=table,
                t_spec=t_spec,
                parent_section_id=spec.id,
            )
            if header_result is not None:
                results.append(header_result)

        # Row count validation
        if t_spec.rows is not None:
            rows_result = _validate_table_rows(
                table=table,
                rows_spec=t_spec.rows,
                table_id=t_spec.id,
                parent_section_id=spec.id,
            )
            if rows_result is not None:
                results.append(rows_result)

    return results


def _validate_table_rows(
    table: Table,
    rows_spec: TableRowsSpec,
    table_id: str,
    parent_section_id: str,
) -> Optional[RuleResult]:
    row_count = len(table.rows)

    if rows_spec.min is not None and row_count < rows_spec.min:
        return RuleResult(
            rule_id="md_table_rows",
            line=table.start_line,
            message=(
                f"Table '{table_id}' in section '{parent_section_id}' "
                f"has {row_count} rows, expected at least {rows_spec.min} rows"
            ),
        )

    if rows_spec.max is not None and row_count > rows_spec.max:
        return RuleResult(
            rule_id="md_table_rows",
            line=table.start_line,
            message=(
                f"Table '{table_id}' in section '{parent_section_id}' "
                f"has {row_count} rows, expected at most {rows_spec.max} rows"
            ),
        )

    return None
