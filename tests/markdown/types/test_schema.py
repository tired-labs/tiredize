# Standard library
from __future__ import annotations

# Local
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
