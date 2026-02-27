# Standard library
from __future__ import annotations

# Third party
import pytest

# Local
from tiredize.markdown.types.document import Document
from tiredize.markdown.types.schema import SchemaConfig
from tiredize.markdown.types.schema import SchemaSection
from tiredize.validators.markdown_schema import AmbiguityError
from tiredize.validators.markdown_schema import validate


# --- Happy path ---


def test_minimal_single_section_matches():
    doc = Document()
    doc.load(text="# Title\n\nSome content\n")
    schema = SchemaConfig(
        sections=[SchemaSection(name="Title")]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_full_trr_document_no_errors():
    doc = Document()
    doc.load(text=(
        "# My Technique Research Report\n\n"
        "## Metadata\n\n"
        "Some metadata\n\n"
        "### Scope Statement\n\n"
        "Scope content\n\n"
        "## Technique Overview\n\n"
        "Overview content\n\n"
        "## Technical Background\n\n"
        "Background content\n\n"
        "## Procedures\n\n"
        "Procedures intro\n\n"
        "### Procedure A: Credential Dumping\n\n"
        "Procedure content\n\n"
        "#### Detection Data Model\n\n"
        "DDM content\n\n"
        "## Available Emulation Tests\n\n"
        "Tests content\n\n"
        "## References\n\n"
        "Reference content\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                pattern=".+",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Metadata",
                        sections=[
                            SchemaSection(
                                level=3,
                                name="Scope Statement",
                                required=False,
                            )
                        ],
                    ),
                    SchemaSection(
                        level=2,
                        name="Technique Overview",
                    ),
                    SchemaSection(
                        level=2,
                        name="Technical Background",
                    ),
                    SchemaSection(
                        level=2,
                        name="Procedures",
                        sections=[
                            SchemaSection(
                                level=3,
                                pattern="Procedure [A-Z]: .+",
                                repeat_min=1,
                                sections=[
                                    SchemaSection(
                                        level=4,
                                        name="Detection Data Model",
                                    )
                                ],
                            )
                        ],
                    ),
                    SchemaSection(
                        level=2,
                        name="Available Emulation Tests",
                    ),
                    SchemaSection(
                        level=2,
                        name="References",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_optional_section_omitted():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "Meta content\n\n"
        "## Body\n\n"
        "Body content\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(
                        level=2,
                        name="Optional Bit",
                        required=False,
                    ),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_multiple_top_level_sections():
    doc = Document()
    doc.load(text=(
        "# Introduction\n\n"
        "Intro content\n\n"
        "# Body\n\n"
        "Body content\n\n"
        "# Conclusion\n\n"
        "Conclusion content\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(name="Introduction"),
            SchemaSection(name="Body"),
            SchemaSection(name="Conclusion"),
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


# --- Missing sections ---


def test_required_section_missing():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Body\n\n"
        "Body content\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids


def test_required_child_missing():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
        "### Procedure A: Recon\n\n"
        "Procedure content\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Procedures",
                        sections=[
                            SchemaSection(
                                level=3,
                                pattern="Procedure [A-Z]: .+",
                                repeat_min=1,
                                sections=[
                                    SchemaSection(
                                        level=4,
                                        name="Detection Data Model",
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids


# --- Unexpected sections ---


def test_unexpected_section_rejected():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Surprise\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


def test_extra_section_allowed():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Surprise\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        allow_extra_sections=True,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


# --- Ordering ---


def test_out_of_order_siblings():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## References\n\n"
        "## Procedures\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Procedures"),
                    SchemaSection(level=2, name="References"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.out_of_order" in rule_ids


# --- Repeating sections ---


def test_repeating_sections_valid():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
        "### Procedure A: Recon\n\n"
        "#### Detection Data Model\n\n"
        "DDM A\n\n"
        "### Procedure B: Exfil\n\n"
        "#### Detection Data Model\n\n"
        "DDM B\n\n"
        "### Procedure C: Persist\n\n"
        "#### Detection Data Model\n\n"
        "DDM C\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Procedures",
                        sections=[
                            SchemaSection(
                                level=3,
                                pattern="Procedure [A-Z]: .+",
                                repeat_min=1,
                                sections=[
                                    SchemaSection(
                                        level=4,
                                        name="Detection Data Model",
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_repeat_below_minimum():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
        "### Procedure A: Solo\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Procedures",
                        sections=[
                            SchemaSection(
                                level=3,
                                pattern="Procedure [A-Z]: .+",
                                repeat_min=2,
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_below_minimum" in rule_ids


def test_repeat_above_maximum():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
        "### Procedure A: Recon\n\n"
        "### Procedure B: Exfil\n\n"
        "### Procedure C: Persist\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Procedures",
                        sections=[
                            SchemaSection(
                                level=3,
                                pattern="Procedure [A-Z]: .+",
                                repeat_max=2,
                                repeat_min=1,
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_above_maximum" in rule_ids


# --- Level mismatch ---


def test_wrong_heading_level():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "### Metadata\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.wrong_level" in rule_ids


# --- Unexpected repeat ---


def test_section_repeated_without_repeat_in_schema():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Metadata\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


# --- Coverage: out-of-order with children ---


def test_out_of_order_section_children_still_validated():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Body\n\n"
        "## Metadata\n\n"
        "### Scope Statement\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Metadata",
                        sections=[
                            SchemaSection(
                                level=3,
                                name="Scope Statement",
                            )
                        ],
                    ),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.out_of_order" in rule_ids
    assert "schema.markdown.missing_section" not in rule_ids


# --- Coverage: unexpected past end of schema ---


def test_unexpected_section_past_end_of_schema():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Straggler\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Metadata",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


# --- Coverage: repeating section skipped by lookahead ---


def test_repeating_section_skipped_to_match_later():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Finale\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Act .+",
                        repeat_min=1,
                    ),
                    SchemaSection(
                        level=2,
                        name="Finale",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_below_minimum" in rule_ids


# --- Coverage: repeating section unvisited at end ---


def test_repeating_section_never_reached():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Prologue\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        name="Prologue",
                    ),
                    SchemaSection(
                        level=2,
                        pattern="Chapter .+",
                        repeat_min=1,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_below_minimum" in rule_ids


# --- Unordered mode ---


def test_unordered_all_present_any_order():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## References\n\n"
        "## Metadata\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                    SchemaSection(
                        level=2, name="References",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_unordered_required_section_missing():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                    SchemaSection(level=2, name="Body"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids


def test_unordered_unexpected_section_rejected():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Surprise\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


def test_unordered_extra_section_allowed():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Metadata\n\n"
        "## Surprise\n\n"
    ))
    schema = SchemaConfig(
        allow_extra_sections=True,
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_unordered_repeat_bounds():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Chapter One\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Chapter .+",
                        repeat_min=2,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_below_minimum" in rule_ids


def test_unordered_duplicate_without_repeat():
    doc = Document()
    doc.load(text=(
        "# Title\n\n"
        "## Procedures\n\n"
        "## Metadata\n\n"
        "## Procedures\n\n"
        "## References\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Title",
                sections=[
                    SchemaSection(
                        level=2, name="Procedures",
                    ),
                    SchemaSection(
                        level=2, name="Metadata",
                    ),
                    SchemaSection(
                        level=2, name="References",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


# --- Ambiguity ---


def test_ordered_ambiguity_raises():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern=".+",
                        required=False,
                    ),
                    SchemaSection(
                        level=2,
                        name="Procedures",
                    ),
                ],
            )
        ]
    )
    with pytest.raises(AmbiguityError, match="Procedures"):
        validate(doc, schema)


def test_unordered_wrong_level_on_non_repeat():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "### Metadata\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.wrong_level" in rule_ids


def test_unordered_wrong_level_on_repeat():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "#### Procedure A: Recon\n\n"
        "#### Procedure B: Exfil\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=3,
                        pattern="Procedure [A-Z]: .+",
                        repeat_min=1,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.wrong_level" in rule_ids


def test_unordered_repeat_with_valid_children():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedure B: Exfil\n\n"
        "### Detection Data Model\n\n"
        "DDM B\n\n"
        "## Procedure A: Recon\n\n"
        "### Detection Data Model\n\n"
        "DDM A\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Procedure [A-Z]: .+",
                        repeat_min=1,
                        sections=[
                            SchemaSection(
                                level=3,
                                name="Detection Data Model",
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_unordered_repeat_with_missing_children():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedure A: Recon\n\n"
        "### Detection Data Model\n\n"
        "DDM A\n\n"
        "## Procedure B: Exfil\n\n"
        "No DDM here!\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Procedure [A-Z]: .+",
                        repeat_min=1,
                        sections=[
                            SchemaSection(
                                level=3,
                                name="Detection Data Model",
                            )
                        ],
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids


def test_unordered_optional_section_omitted():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Body\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Body"),
                    SchemaSection(
                        level=2,
                        name="Appendix",
                        required=False,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_unordered_repeat_above_maximum():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Chapter One\n\n"
        "## Chapter Two\n\n"
        "## Chapter Three\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Chapter .+",
                        repeat_min=1,
                        repeat_max=2,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.repeat_above_maximum" in rule_ids


# --- Matching rules ---


def test_name_match_is_case_sensitive():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## metadata\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(level=2, name="Metadata"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids
    assert "schema.markdown.unexpected_section" in rule_ids


def test_pattern_requires_full_match():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Proc",
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.missing_section" in rule_ids
    assert "schema.markdown.unexpected_section" in rule_ids


def test_unordered_ambiguity_raises():
    doc = Document()
    doc.load(text=(
        "# Report\n\n"
        "## Procedures\n\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Report",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern=".+",
                        required=False,
                    ),
                    SchemaSection(
                        level=2,
                        name="Procedures",
                    ),
                ],
            )
        ]
    )
    with pytest.raises(AmbiguityError, match="Procedures"):
        validate(doc, schema)


# --- Undefined children ---


def test_ordered_undefined_children_rejected():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Fireball\n\n"
        "### Casting Instructions\n\n"
        "Wave your hands dramatically.\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(level=2, name="Fireball"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


def test_ordered_undefined_children_allowed_when_extras_enabled():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Fireball\n\n"
        "### Casting Instructions\n\n"
        "Wave your hands dramatically.\n"
    ))
    schema = SchemaConfig(
        allow_extra_sections=True,
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(level=2, name="Fireball"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_unordered_undefined_children_rejected():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Fireball\n\n"
        "### Casting Instructions\n\n"
        "Wave your hands dramatically.\n"
    ))
    schema = SchemaConfig(
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(level=2, name="Fireball"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


def test_unordered_undefined_children_allowed_when_extras_enabled():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Fireball\n\n"
        "### Casting Instructions\n\n"
        "Wave your hands dramatically.\n"
    ))
    schema = SchemaConfig(
        allow_extra_sections=True,
        enforce_order=False,
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(level=2, name="Fireball"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    assert len(results) == 0


def test_repeating_undefined_children_rejected():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Spell A: Fireball\n\n"
        "### Secret Ingredient\n\n"
        "Dragon breath.\n\n"
        "## Spell B: Ice Storm\n\n"
        "### Secret Ingredient\n\n"
        "Penguin tears.\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(
                        level=2,
                        pattern="Spell [A-Z]: .+",
                        repeat_min=1,
                    ),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.unexpected_section" in rule_ids


def test_out_of_order_undefined_children_rejected():
    doc = Document()
    doc.load(text=(
        "# Spellbook\n\n"
        "## Ingredients\n\n"
        "## Fireball\n\n"
        "### Casting Instructions\n\n"
        "Wave your hands dramatically.\n"
    ))
    schema = SchemaConfig(
        sections=[
            SchemaSection(
                name="Spellbook",
                sections=[
                    SchemaSection(level=2, name="Fireball"),
                    SchemaSection(level=2, name="Ingredients"),
                ],
            )
        ]
    )
    results = validate(doc, schema)
    rule_ids = [r.rule_id for r in results]
    assert "schema.markdown.out_of_order" in rule_ids
    assert "schema.markdown.unexpected_section" in rule_ids
