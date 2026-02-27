# Standard library
from __future__ import annotations
import re

# Local
from tiredize.core_types import Position
from tiredize.core_types import RuleResult
from tiredize.markdown.types.document import Document
from tiredize.markdown.types.schema import SchemaConfig
from tiredize.markdown.types.schema import SchemaSection


class AmbiguityError(Exception):
    pass


def _check_ambiguity(doc_section, schema_sections):
    matches = [
        s for s in schema_sections
        if _name_matches(doc_section, s)
    ]
    if len(matches) > 1:
        title = doc_section.header.title
        entries = ", ".join(
            f"name='{s.name}'" if s.name
            else f"pattern='{s.pattern}'"
            for s in matches
        )
        raise AmbiguityError(
            f"Section '{title}' matches multiple "
            f"schema entries: {entries}"
        )


def _find_root_sections(document):
    claimed = set()
    for section in document.sections:
        for sub in section.subsections:
            claimed.add(sub.header.position.offset)
    return [
        s for s in document.sections
        if s.header.position.offset not in claimed
    ]


def _find_skipped_match(doc_section, skipped):
    for i, schema_section in enumerate(skipped):
        if _name_matches(doc_section, schema_section):
            return i
    return None


def _name_matches(doc_section, schema_section):
    title = doc_section.header.title
    if schema_section.name is not None:
        return title == schema_section.name
    if schema_section.pattern is not None:
        return (
            re.fullmatch(schema_section.pattern, title)
            is not None
        )
    return False


def _validate_ordered(
    doc_sections,
    schema_sections,
    document,
    results,
    allow_extra,
):
    for ds in doc_sections:
        _check_ambiguity(ds, schema_sections)

    doc_ptr = 0
    schema_ptr = 0
    skipped_required: list[SchemaSection] = []

    while doc_ptr < len(doc_sections):
        doc_section = doc_sections[doc_ptr]

        # Check against previously skipped required entries
        skipped_idx = _find_skipped_match(
            doc_section, skipped_required
        )
        if skipped_idx is not None:
            skipped_schema = skipped_required.pop(
                skipped_idx
            )
            results.append(RuleResult(
                message=(
                    f"Section "
                    f"'{doc_section.header.title}' "
                    f"is out of order"
                ),
                position=doc_section.header.position,
                rule_id="schema.markdown.out_of_order",
            ))
            _validate_ordered(
                doc_section.subsections,
                skipped_schema.sections,
                document, results, allow_extra,
            )
            doc_ptr += 1
            continue

        # Past end of schema entries
        if schema_ptr >= len(schema_sections):
            if not allow_extra:
                results.append(RuleResult(
                    message=(
                        f"Unexpected section "
                        f"'{doc_section.header.title}'"
                    ),
                    position=doc_section.header.position,
                    rule_id=(
                        "schema.markdown.unexpected_section"
                    ),
                ))
            doc_ptr += 1
            continue

        schema_entry = schema_sections[schema_ptr]

        if _name_matches(doc_section, schema_entry):
            # Check level
            if (doc_section.header.level
                    != schema_entry.level):
                results.append(RuleResult(
                    message=(
                        f"Section "
                        f"'{doc_section.header.title}' "
                        f"is level "
                        f"{doc_section.header.level}, "
                        f"expected {schema_entry.level}"
                    ),
                    position=doc_section.header.position,
                    rule_id="schema.markdown.wrong_level",
                ))

            # Repeating section
            if schema_entry.repeat_min is not None:
                count = _consume_repeating(
                    doc_sections, doc_ptr,
                    schema_entry, document,
                    results, allow_extra,
                )
                doc_ptr += count
                _check_repeat_bounds(
                    schema_entry, count, results
                )
            else:
                # Non-repeating match
                _validate_ordered(
                    doc_section.subsections,
                    schema_entry.sections,
                    document, results, allow_extra,
                )
                doc_ptr += 1

            schema_ptr += 1
        else:
            # Look ahead for a match in remaining schema
            found_later = _find_later_match(
                doc_section, schema_sections,
                schema_ptr + 1,
            )

            if found_later is not None:
                _skip_schema_entries(
                    schema_sections, schema_ptr,
                    found_later, skipped_required,
                    results,
                )
                schema_ptr = found_later
            else:
                if not allow_extra:
                    results.append(RuleResult(
                        message=(
                            f"Unexpected section "
                            f"'{doc_section.header.title}'"
                        ),
                        position=(
                            doc_section.header.position
                        ),
                        rule_id=(
                            "schema.markdown"
                            ".unexpected_section"
                        ),
                    ))
                doc_ptr += 1

    # Remaining skipped required entries
    for skipped in skipped_required:
        results.append(RuleResult(
            message=(
                f"Missing required section: "
                f"'{skipped.name or skipped.pattern}'"
            ),
            position=Position(offset=0, length=0),
            rule_id="schema.markdown.missing_section",
        ))

    # Remaining unvisited schema entries
    _emit_remaining_schema_errors(
        schema_sections, schema_ptr, results
    )


def _consume_repeating(
    doc_sections,
    start_ptr,
    schema_entry,
    document,
    results,
    allow_extra,
):
    count = 0
    ptr = start_ptr
    while (ptr < len(doc_sections)
           and _name_matches(
               doc_sections[ptr], schema_entry
           )):
        doc_section = doc_sections[ptr]
        _validate_ordered(
            doc_section.subsections,
            schema_entry.sections,
            document, results, allow_extra,
        )
        count += 1
        ptr += 1
    return count


def _check_repeat_bounds(schema_entry, count, results):
    label = schema_entry.name or schema_entry.pattern
    if count < schema_entry.repeat_min:
        results.append(RuleResult(
            message=(
                f"Section matching '{label}' "
                f"appears {count} time(s), "
                f"minimum is {schema_entry.repeat_min}"
            ),
            position=Position(offset=0, length=0),
            rule_id=(
                "schema.markdown.repeat_below_minimum"
            ),
        ))
    if (schema_entry.repeat_max is not None
            and count > schema_entry.repeat_max):
        results.append(RuleResult(
            message=(
                f"Section matching '{label}' "
                f"appears {count} time(s), "
                f"maximum is {schema_entry.repeat_max}"
            ),
            position=Position(offset=0, length=0),
            rule_id=(
                "schema.markdown.repeat_above_maximum"
            ),
        ))


def _find_later_match(doc_section, schema_sections, start):
    for j in range(start, len(schema_sections)):
        if _name_matches(doc_section, schema_sections[j]):
            return j
    return None


def _skip_schema_entries(
    schema_sections,
    start,
    end,
    skipped_required,
    results,
):
    for k in range(start, end):
        entry = schema_sections[k]
        if entry.repeat_min is not None:
            if entry.repeat_min > 0:
                results.append(RuleResult(
                    message=(
                        f"Section matching "
                        f"'{entry.name or entry.pattern}'"
                        f" appears 0 time(s), minimum "
                        f"is {entry.repeat_min}"
                    ),
                    position=Position(offset=0, length=0),
                    rule_id=(
                        "schema.markdown"
                        ".repeat_below_minimum"
                    ),
                ))
        elif entry.required:
            skipped_required.append(entry)


def _emit_remaining_schema_errors(
    schema_sections, schema_ptr, results
):
    while schema_ptr < len(schema_sections):
        entry = schema_sections[schema_ptr]
        if entry.repeat_min is not None:
            if entry.repeat_min > 0:
                results.append(RuleResult(
                    message=(
                        f"Section matching "
                        f"'{entry.name or entry.pattern}'"
                        f" appears 0 time(s), minimum "
                        f"is {entry.repeat_min}"
                    ),
                    position=Position(
                        offset=0, length=0
                    ),
                    rule_id=(
                        "schema.markdown"
                        ".repeat_below_minimum"
                    ),
                ))
        elif entry.required:
            results.append(RuleResult(
                message=(
                    f"Missing required section: "
                    f"'{entry.name or entry.pattern}'"
                ),
                position=Position(
                    offset=0, length=0
                ),
                rule_id=(
                    "schema.markdown.missing_section"
                ),
            ))
        schema_ptr += 1


def _validate_unordered(
    doc_sections,
    schema_sections,
    document,
    results,
    allow_extra,
):
    for ds in doc_sections:
        _check_ambiguity(ds, schema_sections)

    claimed = set()

    for schema_entry in schema_sections:
        matches = [
            (i, ds) for i, ds in enumerate(doc_sections)
            if _name_matches(ds, schema_entry)
        ]
        count = len(matches)

        if schema_entry.repeat_min is not None:
            for i, ds in matches:
                claimed.add(i)
                if ds.header.level != schema_entry.level:
                    results.append(RuleResult(
                        message=(
                            f"Section "
                            f"'{ds.header.title}' "
                            f"is level "
                            f"{ds.header.level}, "
                            f"expected "
                            f"{schema_entry.level}"
                        ),
                        position=ds.header.position,
                        rule_id=(
                            "schema.markdown.wrong_level"
                        ),
                    ))
                _validate_unordered(
                    ds.subsections,
                    schema_entry.sections,
                    document, results, allow_extra,
                )
            _check_repeat_bounds(
                schema_entry, count, results
            )
        else:
            if count == 0:
                if schema_entry.required:
                    label = (
                        schema_entry.name
                        or schema_entry.pattern
                    )
                    results.append(RuleResult(
                        message=(
                            f"Missing required section: "
                            f"'{label}'"
                        ),
                        position=Position(
                            offset=0, length=0
                        ),
                        rule_id=(
                            "schema.markdown"
                            ".missing_section"
                        ),
                    ))
            else:
                first_i, first_ds = matches[0]
                claimed.add(first_i)
                if (first_ds.header.level
                        != schema_entry.level):
                    results.append(RuleResult(
                        message=(
                            f"Section "
                            f"'{first_ds.header.title}'"
                            f" is level "
                            f"{first_ds.header.level}, "
                            f"expected "
                            f"{schema_entry.level}"
                        ),
                        position=(
                            first_ds.header.position
                        ),
                        rule_id=(
                            "schema.markdown.wrong_level"
                        ),
                    ))
                _validate_unordered(
                    first_ds.subsections,
                    schema_entry.sections,
                    document, results, allow_extra,
                )
                for i, ds in matches[1:]:
                    if not allow_extra:
                        results.append(RuleResult(
                            message=(
                                f"Unexpected section "
                                f"'{ds.header.title}'"
                            ),
                            position=ds.header.position,
                            rule_id=(
                                "schema.markdown"
                                ".unexpected_section"
                            ),
                        ))

    if not allow_extra:
        for i, ds in enumerate(doc_sections):
            if i not in claimed:
                results.append(RuleResult(
                    message=(
                        f"Unexpected section "
                        f"'{ds.header.title}'"
                    ),
                    position=ds.header.position,
                    rule_id=(
                        "schema.markdown"
                        ".unexpected_section"
                    ),
                ))


def validate(
    document: Document,
    schema: SchemaConfig,
) -> list[RuleResult]:
    results: list[RuleResult] = []
    roots = _find_root_sections(document)
    if schema.enforce_order:
        _validate_ordered(
            roots, schema.sections,
            document, results,
            schema.allow_extra_sections,
        )
    else:
        _validate_unordered(
            roots, schema.sections,
            document, results,
            schema.allow_extra_sections,
        )
    return results
