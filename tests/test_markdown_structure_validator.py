from tiredize.document import Document
from tiredize.types import RuleResult
from tiredize.validators.markdown_structure import validate_markdown_structure
import textwrap
import yaml


def make_doc(md: str) -> Document:
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


def load_schema_cfg(yaml_text: str) -> dict:
    yaml_text = textwrap.dedent(yaml_text).lstrip("\n")
    return yaml.safe_load(yaml_text)


BASIC_SCHEMA_YAML = """
markdown:
  sections:
    - id: intro
      title: "Introduction"
      level: 2
      required: true
      repeatable: false

    - id: procedures
      title: "Procedures"
      level: 2
      required: true
      repeatable: false

      children:
        - id: procedure_block
          title_pattern: "^Procedure [A-Za-z0-9_]+: .+$"
          level: 3
          required: true
          repeatable: true

      tables:
        - id: procedures_table
          required: true
          repeatable: false
          header:
            match: exact
            columns:
              - "Procedure Id"
              - "Name"
              - "Primary Tactic"
              - "Description"
          rows:
            min: 1
            max: null

    - id: references
      title: "References"
      level: 2
      required: true
      repeatable: false
"""

BASIC_SCHEMA_CFG = load_schema_cfg(BASIC_SCHEMA_YAML)


def test_markdown_structure_all_sections_and_table_present():
    md = """
    # Title

    ## Introduction

    Some intro text.

    ## Procedures

    | Procedure Id | Name | Primary Tactic | Description |
    | ------------ | ---- | -------------- | ----------- |
    | TRR0001.A    | Foo  | Execution      | Example     |

    ### Procedure Alpha: Example

    Details for procedure alpha.

    ## References

    - Item 1
    """

    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    assert isinstance(results, list)
    assert len(results) == 0, "Expected no structural findings for a valid"
    "document"


def test_missing_required_top_level_section():
    md = """
    # Title

    ## Introduction

    Some intro text.

    ## Procedures

    | Procedure Id | Name | Primary Tactic | Description |
    | ------------ | ---- | -------------- | ----------- |
    | TRR0001.A    | Foo  | Execution      | Example     |
    """

    # No References section
    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    # We only care that the missing References section is detected.
    missing_refs = [
        r for r in results
        if r.rule_id == "md_section_missing"
        and "references" in r.message.lower()
    ]
    assert len(missing_refs) == 1
    assert isinstance(missing_refs[0], RuleResult)


def test_missing_required_child_section_under_procedures():
    md = """
    # Title

    ## Introduction

    Text.

    ## Procedures

    | Procedure Id | Name | Primary Tactic | Description |
    | ------------ | ---- | -------------- | ----------- |
    | TRR0001.A    | Foo  | Execution      | Example     |

    ## References

    - Reference
    """

    # There is no H3 Procedure block under Procedures
    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    child_missing = [
        r for r in results
        if r.rule_id == "md_section_missing"
        and "procedure_block" in r.message
    ]
    assert len(child_missing) == 1
    assert isinstance(child_missing[0], RuleResult)


def test_procedure_child_sections_present():
    md = """
    # Title

    ## Introduction

    Intro text.

    ## Procedures

    | Procedure Id | Name | Primary Tactic | Description |
    | ------------ | ---- | -------------- | ----------- |
    | TRR0001.A    | Foo  | Execution      | Example     |

    ### Procedure Alpha: Example

    Details for procedure alpha.

    ### Procedure Beta: Another

    Details for procedure beta.

    ## References

    - R1
    """

    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    # No missing child section errors should be present
    missing_children = [
        r for r in results
        if r.rule_id == "md_section_missing"
        and "procedure_block" in r.message
    ]
    assert len(missing_children) == 0


def test_missing_required_table_under_procedures():
    md = """
    # Title

    ## Introduction

    Intro.

    ## Procedures

    ### Procedure Alpha: Example

    Details.

    ## References

    - R1
    """

    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    table_missing = [
        r for r in results
        if r.rule_id == "md_table_missing"
        and "procedures_table" in r.message
    ]
    assert len(table_missing) == 1
    assert isinstance(table_missing[0], RuleResult)


def test_table_header_mismatch_detected():
    md = """
    # Title

    ## Introduction

    Intro.

    ## Procedures

    | Procedure Id | Name | Description |
    | ------------ | ---- | ----------- |
    | TRR0001.A    | Foo  | Example     |

    ### Procedure Alpha: Example

    Details.

    ## References

    - R1
    """

    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    header_errors = [
        r for r in results
        if r.rule_id == "md_table_header"
        and "procedures_table" in r.message
    ]
    assert len(header_errors) == 1
    assert isinstance(header_errors[0], RuleResult)


def test_table_rows_min_enforced():
    # Same schema, which has rows.min = 1 for procedures_table
    md = """
    # Title

    ## Introduction

    Intro.

    ## Procedures

    | Procedure Id | Name | Primary Tactic | Description |
    | ------------ | ---- | -------------- | ----------- |
    """

    # Header only, no data rows
    doc = make_doc(md)
    results = validate_markdown_structure(doc, BASIC_SCHEMA_CFG)

    row_errors = [
        r for r in results
        if r.rule_id == "md_table_rows"
        and "procedures_table" in r.message
        and "at least 1 rows" in r.message
    ]
    assert len(row_errors) == 1


def test_table_rows_max_enforced():
    # Schema with a small max row count for procedures_table
    schema_yaml = """
    markdown:
      sections:
        - id: procedures
          title: "Procedures"
          level: 2
          required: true
          repeatable: false
          tables:
            - id: procedures_table
              required: true
              repeatable: false
              header:
                match: exact
                columns:
                  - "Procedure Id"
                  - "Name"
              rows:
                min: 0
                max: 2
    """
    schema_cfg = load_schema_cfg(schema_yaml)

    md = """
    # Title

    ## Procedures

    | Procedure Id | Name |
    | ------------ | ---- |
    | TRR0001.A    | Foo  |
    | TRR0002.B    | Bar  |
    | TRR0003.C    | Baz  |
    """

    doc = make_doc(md)
    results = validate_markdown_structure(doc, schema_cfg)

    row_errors = [
        r for r in results
        if r.rule_id == "md_table_rows"
        and "procedures_table" in r.message
        and "at most 2 rows" in r.message
    ]
    assert len(row_errors) == 1
