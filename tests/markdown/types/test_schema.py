# Standard library
from __future__ import annotations

# Third-party
import pytest

# Local
from tiredize.markdown.types.schema import load_schema
from tiredize.markdown.types.schema import SchemaConfig
from tiredize.markdown.types.schema import SchemaSection


def test_single_level1_header_all_defaults():
    config = SchemaConfig(
        sections=[
            SchemaSection(name="Title")
        ]
    )

    assert config.enforce_order is True
    assert config.allow_extra_sections is False
    assert len(config.sections) == 1

    section = config.sections[0]
    assert section.name == "Title"
    assert section.pattern is None
    assert section.level == 1
    assert section.required is True
    assert section.repeat_min is None
    assert section.repeat_max is None
    assert section.sections == []


def test_trr_schema_full():
    config = SchemaConfig(
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

    assert config.enforce_order is True
    assert config.allow_extra_sections is False
    assert len(config.sections) == 1

    root = config.sections[0]
    assert root.pattern == ".+"
    assert root.level == 1
    assert len(root.sections) == 6

    metadata = root.sections[0]
    assert metadata.name == "Metadata"
    assert metadata.level == 2
    assert len(metadata.sections) == 1
    assert metadata.sections[0].name == "Scope Statement"
    assert metadata.sections[0].required is False

    procedures = root.sections[3]
    assert procedures.name == "Procedures"
    assert len(procedures.sections) == 1

    procedure = procedures.sections[0]
    assert procedure.pattern == "Procedure [A-Z]: .+"
    assert procedure.repeat_min == 1
    assert procedure.repeat_max is None
    assert len(procedure.sections) == 1
    assert procedure.sections[0].name == "Detection Data Model"
    assert procedure.sections[0].level == 4


# --- Loader: happy path ---


def test_load_minimal_config():
    yaml_str = """
sections:
  - name: "Title"
"""
    config = load_schema(yaml_str)

    assert config.enforce_order is True
    assert config.allow_extra_sections is False
    assert len(config.sections) == 1

    section = config.sections[0]
    assert section.name == "Title"
    assert section.pattern is None
    assert section.level == 1
    assert section.required is True
    assert section.repeat_min is None
    assert section.repeat_max is None
    assert section.sections == []


def test_load_trr_schema():
    yaml_str = """
enforce_order: true
allow_extra_sections: false
sections:
  - pattern: ".+"
    sections:
      - name: "Metadata"
        level: 2
        sections:
          - name: "Scope Statement"
            level: 3
            required: false
      - name: "Technique Overview"
        level: 2
      - name: "Technical Background"
        level: 2
      - name: "Procedures"
        level: 2
        sections:
          - pattern: "Procedure [A-Z]: .+"
            level: 3
            repeat: true
            sections:
              - name: "Detection Data Model"
                level: 4
      - name: "Available Emulation Tests"
        level: 2
      - name: "References"
        level: 2
"""
    config = load_schema(yaml_str)

    assert len(config.sections) == 1

    root = config.sections[0]
    assert root.pattern == ".+"
    assert root.level == 1
    assert len(root.sections) == 6

    metadata = root.sections[0]
    assert metadata.name == "Metadata"
    assert len(metadata.sections) == 1
    assert metadata.sections[0].name == "Scope Statement"
    assert metadata.sections[0].required is False

    procedures = root.sections[3]
    assert procedures.name == "Procedures"

    procedure = procedures.sections[0]
    assert procedure.pattern == "Procedure [A-Z]: .+"
    assert procedure.repeat_min == 1
    assert procedure.repeat_max is None
    assert len(procedure.sections) == 1
    assert procedure.sections[0].name == "Detection Data Model"
    assert procedure.sections[0].level == 4


def test_load_explicit_top_level_flags():
    yaml_str = """
enforce_order: false
allow_extra_sections: true
sections:
  - name: "Anything Goes"
"""
    config = load_schema(yaml_str)

    assert config.enforce_order is False
    assert config.allow_extra_sections is True


def test_load_repeat_true():
    yaml_str = """
sections:
  - name: "Repeatable"
    repeat: true
"""
    config = load_schema(yaml_str)
    section = config.sections[0]

    assert section.repeat_min == 1
    assert section.repeat_max is None


def test_load_repeat_bounded():
    yaml_str = """
sections:
  - name: "Bounded"
    repeat:
      min: 2
      max: 5
"""
    config = load_schema(yaml_str)
    section = config.sections[0]

    assert section.repeat_min == 2
    assert section.repeat_max == 5


def test_load_repeat_min_only():
    yaml_str = """
sections:
  - name: "At Least Three"
    repeat:
      min: 3
"""
    config = load_schema(yaml_str)
    section = config.sections[0]

    assert section.repeat_min == 3
    assert section.repeat_max is None


def test_load_level_inference():
    yaml_str = """
sections:
  - name: "Root"
    sections:
      - name: "Child"
        sections:
          - name: "Grandchild"
"""
    config = load_schema(yaml_str)

    root = config.sections[0]
    assert root.level == 1

    child = root.sections[0]
    assert child.level == 2

    grandchild = child.sections[0]
    assert grandchild.level == 3


# --- Loader: validation errors ---


def test_load_rejects_name_and_pattern():
    yaml_str = """
sections:
  - name: "Oops"
    pattern: ".+"
"""
    with pytest.raises(ValueError):
        load_schema(yaml_str)


def test_load_rejects_neither_name_nor_pattern():
    yaml_str = """
sections:
  - level: 1
"""
    with pytest.raises(ValueError):
        load_schema(yaml_str)


def test_load_rejects_child_level_equal_to_parent():
    yaml_str = """
sections:
  - name: "Root"
    sections:
      - name: "Not A Child"
        level: 1
"""
    with pytest.raises(ValueError):
        load_schema(yaml_str)


def test_load_rejects_child_level_lower_than_parent():
    yaml_str = """
sections:
  - name: "Parent"
    level: 3
    sections:
      - name: "Impostor"
        level: 2
"""
    with pytest.raises(ValueError):
        load_schema(yaml_str)


# --- Loader: None / non-dict handling ---


def test_load_empty_string():
    config = load_schema("")
    assert config.sections == []
    assert config.enforce_order is True
    assert config.allow_extra_sections is False


def test_load_scalar_rejected():
    with pytest.raises(ValueError, match="YAML mapping"):
        load_schema("42")


# --- Loader: repeat bound validation ---


def test_load_repeat_min_negative():
    yaml_str = """
sections:
  - name: "Cursed"
    repeat:
      min: -1
"""
    with pytest.raises(ValueError, match="negative"):
        load_schema(yaml_str)


def test_load_repeat_max_negative():
    yaml_str = """
sections:
  - name: "Doomed"
    repeat:
      min: 0
      max: -5
"""
    with pytest.raises(ValueError, match="negative"):
        load_schema(yaml_str)


def test_load_repeat_min_non_integer():
    yaml_str = """
sections:
  - name: "Confused"
    repeat:
      min: "three"
"""
    with pytest.raises(ValueError, match="integer"):
        load_schema(yaml_str)


def test_load_repeat_max_non_integer():
    yaml_str = """
sections:
  - name: "Baffled"
    repeat:
      min: 1
      max: "plenty"
"""
    with pytest.raises(ValueError, match="integer"):
        load_schema(yaml_str)


def test_load_repeat_max_less_than_min():
    yaml_str = """
sections:
  - name: "Backwards"
    repeat:
      min: 5
      max: 2
"""
    with pytest.raises(ValueError, match="less than"):
        load_schema(yaml_str)


# --- Loader: regex pattern validation ---


def test_load_invalid_regex_pattern():
    yaml_str = """
sections:
  - pattern: "["
"""
    with pytest.raises(ValueError, match="Invalid regex"):
        load_schema(yaml_str)
