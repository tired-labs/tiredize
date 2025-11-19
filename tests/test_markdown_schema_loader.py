# tests/test_markdown_schema_loader.py

import textwrap
import yaml

from tiredize.markdown_schema import (
    load_markdown_schema,
    MarkdownSchema,
    SectionSpec,
    TableSpec,
    TableHeaderSpec,
    TableRowsSpec,
)


def load_yaml(yaml_text: str) -> dict:
    yaml_text = textwrap.dedent(yaml_text).lstrip("\n")
    return yaml.safe_load(yaml_text)


def test_load_simple_sections_and_tables():
    cfg_yaml = """
    markdown:
      sections:
        - id: technical_background
          title: "Technical Background"
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

              children:
                - id: procedure_ddm
                  title: "Detection Data Model"
                  level: 4
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

    cfg = load_yaml(cfg_yaml)
    schema = load_markdown_schema(cfg)

    assert isinstance(schema, MarkdownSchema)
    assert len(schema.sections) == 3

    tech = schema.sections[0]
    procedures = schema.sections[1]
    references = schema.sections[2]

    # Technical Background section
    assert isinstance(tech, SectionSpec)
    assert tech.id == "technical_background"
    assert tech.title == "Technical Background"
    assert tech.level == 2
    assert tech.required is True
    assert tech.repeatable is False
    assert tech.children == []
    assert tech.tables == []

    # Procedures section
    assert procedures.id == "procedures"
    assert procedures.title == "Procedures"
    assert procedures.level == 2
    assert procedures.required is True
    assert procedures.repeatable is False

    # One child section: procedure_block
    assert len(procedures.children) == 1
    proc_block = procedures.children[0]
    assert proc_block.id == "procedure_block"
    assert proc_block.title is None
    assert proc_block.title_pattern == "^Procedure [A-Za-z0-9_]+: .+$"
    assert proc_block.level == 3
    assert proc_block.required is True
    assert proc_block.repeatable is True

    # Child of procedure_block: procedure_ddm
    assert len(proc_block.children) == 1
    ddm = proc_block.children[0]
    assert ddm.id == "procedure_ddm"
    assert ddm.title == "Detection Data Model"
    assert ddm.title_pattern is None
    assert ddm.level == 4
    assert ddm.required is True
    assert ddm.repeatable is False

    # Procedures tables
    assert len(procedures.tables) == 1
    table = procedures.tables[0]
    assert isinstance(table, TableSpec)
    assert table.id == "procedures_table"
    assert table.required is True
    assert table.repeatable is False

    # Header spec
    assert isinstance(table.header, TableHeaderSpec)
    assert table.header.match == "exact"
    assert table.header.columns == [
        "Procedure Id",
        "Name",
        "Primary Tactic",
        "Description",
    ]

    # Rows spec
    assert isinstance(table.rows, TableRowsSpec)
    assert table.rows.min == 1
    assert table.rows.max is None

    # References section
    assert references.id == "references"
    assert references.title == "References"
    assert references.level == 2
    assert references.required is True
    assert references.repeatable is False
    assert references.children == []
    assert references.tables == []


def test_section_must_have_title_or_pattern():
    cfg_yaml = """
    markdown:
      sections:
        - id: bad_section
          level: 2
          required: true
    """
    cfg = load_yaml(cfg_yaml)

    try:
        load_markdown_schema(cfg)
    except ValueError as e:
        msg = str(e)
        assert "bad_section" in msg
        assert "title" in msg or "title_pattern" in msg
    else:
        assert False, "Expected ValueError for section without title or "
        "title_pattern"


def test_missing_markdown_key_raises():
    cfg_yaml = """
    not_markdown:
      sections: []
    """
    cfg = load_yaml(cfg_yaml)

    try:
        load_markdown_schema(cfg)
    except ValueError as e:
        assert "markdown" in str(e)
    else:
        assert False, "Expected ValueError for missing 'markdown' key"
