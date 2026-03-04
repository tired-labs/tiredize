# Standard library
from __future__ import annotations

# Third party
import pytest

# Local
from tiredize.validators.frontmatter_schema import (
    load_frontmatter_schema,
    safe_load_yaml,
    validate,
)
from tiredize.markdown.types.document import Document


# ============================================================
# safe_load_yaml — duplicate key detection
# ============================================================


class TestSafeLoadYaml:
    """Custom YAML loader that rejects duplicate keys."""

    def test_simple_mapping(self):
        result = safe_load_yaml("name: Falkor\nage: 42\n")
        assert result == {"name": "Falkor", "age": 42}

    def test_empty_string_returns_none(self):
        assert safe_load_yaml("") is None

    def test_scalar_returns_scalar(self):
        assert safe_load_yaml("42") == 42

    def test_list_returns_list(self):
        assert safe_load_yaml("- one\n- two\n") == ["one", "two"]

    def test_duplicate_key_raises(self):
        with pytest.raises(ValueError, match="duplicate key.*name"):
            safe_load_yaml("name: Artax\nname: Falkor\n")

    def test_duplicate_key_different_values(self):
        with pytest.raises(ValueError, match="duplicate key.*tactics"):
            safe_load_yaml(
                "tactics:\n  - Recon\ntactics:\n  - Execution\n"
            )

    def test_duplicate_key_same_value(self):
        # Even identical values are an error — the key is duplicated
        with pytest.raises(ValueError, match="duplicate key.*x"):
            safe_load_yaml("x: 1\nx: 1\n")

    def test_non_duplicate_keys_pass(self):
        result = safe_load_yaml(
            "title: The Neverending Story\n"
            "author: Michael Ende\n"
            "year: 1979\n"
        )
        assert result == {
            "title": "The Neverending Story",
            "author": "Michael Ende",
            "year": 1979,
        }


# ============================================================
# load_frontmatter_schema — schema self-validation
# ============================================================


class TestLoadSchemaHappyPath:
    """Valid schemas load without error."""

    def test_minimal_schema_one_field(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  title:\n"
            "    type: string\n"
        )
        assert "title" in schema.fields
        assert schema.fields["title"].type == "string"
        assert schema.fields["title"].required is True
        assert schema.fields["title"].allowed is None
        assert schema.allow_extra_fields is False

    def test_all_scalar_types(self):
        yaml_str = (
            "fields:\n"
            "  name:\n    type: string\n"
            "  count:\n    type: int\n"
            "  ratio:\n    type: float\n"
            "  draft:\n    type: bool\n"
            "  created:\n    type: date\n"
            "  tags:\n    type: list\n"
        )
        schema = load_frontmatter_schema(yaml_str)
        assert schema.fields["name"].type == "string"
        assert schema.fields["count"].type == "int"
        assert schema.fields["ratio"].type == "float"
        assert schema.fields["draft"].type == "bool"
        assert schema.fields["created"].type == "date"
        assert schema.fields["tags"].type == "list"

    def test_required_false_explicit(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  draft:\n"
            "    type: bool\n"
            "    required: false\n"
        )
        assert schema.fields["draft"].required is False

    def test_required_true_explicit(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  title:\n"
            "    type: string\n"
            "    required: true\n"
        )
        assert schema.fields["title"].required is True

    def test_allowed_on_string_field(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  status:\n"
            "    type: string\n"
            "    allowed:\n"
            "      - draft\n"
            "      - ready\n"
            "      - done\n"
        )
        assert schema.fields["status"].allowed == [
            "draft", "ready", "done"
        ]

    def test_allowed_on_int_field(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  priority:\n"
            "    type: int\n"
            "    allowed:\n"
            "      - 1\n"
            "      - 2\n"
            "      - 3\n"
        )
        assert schema.fields["priority"].allowed == [1, 2, 3]

    def test_allowed_on_list_field(self):
        schema = load_frontmatter_schema(
            "fields:\n"
            "  tactics:\n"
            "    type: list\n"
            "    allowed:\n"
            "      - Recon\n"
            "      - Execution\n"
        )
        assert schema.fields["tactics"].allowed == [
            "Recon", "Execution"
        ]

    def test_allow_extra_fields_true(self):
        schema = load_frontmatter_schema(
            "allow_extra_fields: true\n"
            "fields:\n"
            "  title:\n"
            "    type: string\n"
        )
        assert schema.allow_extra_fields is True

    def test_allow_extra_fields_false_explicit(self):
        schema = load_frontmatter_schema(
            "allow_extra_fields: false\n"
            "fields:\n"
            "  title:\n"
            "    type: string\n"
        )
        assert schema.allow_extra_fields is False

    def test_empty_fields_map(self):
        schema = load_frontmatter_schema("fields: {}\n")
        assert schema.fields == {}

    def test_full_issue_schema(self):
        """Real-world schema: tiredize issue files."""
        schema = load_frontmatter_schema(
            "allow_extra_fields: false\n"
            "fields:\n"
            "  status:\n"
            "    type: string\n"
            "    allowed:\n"
            "      - draft\n"
            "      - ready\n"
            "      - active\n"
            "      - done\n"
            "  type:\n"
            "    type: string\n"
            "    allowed:\n"
            "      - bug\n"
            "      - feature\n"
            "  priority:\n"
            "    type: string\n"
            "    allowed:\n"
            "      - critical\n"
            "      - high\n"
            "      - medium\n"
            "      - low\n"
            "  created:\n"
            "    type: date\n"
            "  parent:\n"
            "    type: string\n"
            "    required: false\n"
            "  sub_issues:\n"
            "    type: list\n"
            "    required: false\n"
            "  labels:\n"
            "    type: list\n"
            "    required: false\n"
        )
        assert len(schema.fields) == 7
        assert schema.fields["status"].required is True
        assert schema.fields["parent"].required is False


class TestLoadSchemaErrors:
    """Invalid schemas raise ValueError."""

    def test_non_mapping_yaml(self):
        with pytest.raises(ValueError, match="mapping"):
            load_frontmatter_schema("- just\n- a\n- list\n")

    def test_empty_string(self):
        # Empty YAML is None -> treated as empty mapping -> no fields
        # key is required
        with pytest.raises(ValueError, match="fields"):
            load_frontmatter_schema("")

    def test_missing_fields_key(self):
        with pytest.raises(ValueError, match="fields"):
            load_frontmatter_schema("allow_extra_fields: true\n")

    def test_fields_not_a_mapping(self):
        with pytest.raises(ValueError, match="mapping"):
            load_frontmatter_schema("fields:\n  - title\n  - date\n")

    def test_unknown_top_level_key(self):
        with pytest.raises(ValueError, match="enforce_order"):
            load_frontmatter_schema(
                "enforce_order: true\n"
                "fields:\n"
                "  title:\n"
                "    type: string\n"
            )

    def test_unknown_field_property(self):
        with pytest.raises(ValueError, match="pattern"):
            load_frontmatter_schema(
                "fields:\n"
                "  title:\n"
                "    type: string\n"
                "    pattern: '.+'\n"
            )

    def test_missing_type(self):
        with pytest.raises(ValueError, match="type"):
            load_frontmatter_schema(
                "fields:\n"
                "  title:\n"
                "    required: true\n"
            )

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="enum"):
            load_frontmatter_schema(
                "fields:\n"
                "  status:\n"
                "    type: enum\n"
            )

    def test_required_not_bool(self):
        with pytest.raises(ValueError, match="bool"):
            load_frontmatter_schema(
                "fields:\n"
                "  title:\n"
                "    type: string\n"
                "    required: yes_please\n"
            )

    def test_allowed_not_a_list(self):
        with pytest.raises(ValueError, match="list"):
            load_frontmatter_schema(
                "fields:\n"
                "  status:\n"
                "    type: string\n"
                "    allowed: draft\n"
            )

    def test_allowed_empty_list(self):
        with pytest.raises(ValueError, match="empty"):
            load_frontmatter_schema(
                "fields:\n"
                "  status:\n"
                "    type: string\n"
                "    allowed: []\n"
            )

    def test_allowed_type_mismatch_string_field_int_value(self):
        with pytest.raises(ValueError, match="allowed.*type"):
            load_frontmatter_schema(
                "fields:\n"
                "  status:\n"
                "    type: string\n"
                "    allowed:\n"
                "      - 42\n"
            )

    def test_allowed_type_mismatch_int_field_string_value(self):
        with pytest.raises(ValueError, match="allowed.*type"):
            load_frontmatter_schema(
                "fields:\n"
                "  priority:\n"
                "    type: int\n"
                "    allowed:\n"
                "      - high\n"
            )

    def test_allowed_type_mismatch_list_field_int_value(self):
        # allowed on list means each allowed value must be a string
        with pytest.raises(ValueError, match="allowed.*string"):
            load_frontmatter_schema(
                "fields:\n"
                "  tags:\n"
                "    type: list\n"
                "    allowed:\n"
                "      - 42\n"
            )

    def test_allow_extra_fields_not_bool(self):
        with pytest.raises(ValueError, match="bool"):
            load_frontmatter_schema(
                "allow_extra_fields: maybe\n"
                "fields:\n"
                "  title:\n"
                "    type: string\n"
            )

    def test_field_definition_not_a_mapping(self):
        with pytest.raises(ValueError, match="mapping"):
            load_frontmatter_schema(
                "fields:\n"
                "  title: string\n"
            )

    def test_allowed_bool_in_int_field(self):
        """bool is subclass of int; allowed values must reject bool."""
        with pytest.raises(ValueError, match="allowed.*type"):
            load_frontmatter_schema(
                "fields:\n"
                "  count:\n"
                "    type: int\n"
                "    allowed:\n"
                "      - true\n"
            )

    def test_field_name_bool_rejected(self):
        """YAML parses bare 'true' as a boolean key, not a string.
        Schema loader must reject non-string field names."""
        with pytest.raises(ValueError, match="[Ff]ield name.*string"):
            load_frontmatter_schema(
                "fields:\n"
                "  true:\n"
                "    type: bool\n"
            )

    def test_field_name_null_rejected(self):
        """YAML parses bare 'null' as None. Schema loader must reject."""
        with pytest.raises(ValueError, match="[Ff]ield name.*string"):
            load_frontmatter_schema(
                "fields:\n"
                "  null:\n"
                "    type: string\n"
            )

    def test_field_name_int_rejected(self):
        """YAML parses bare '42' as an integer key."""
        with pytest.raises(ValueError, match="[Ff]ield name.*string"):
            load_frontmatter_schema(
                "fields:\n"
                "  42:\n"
                "    type: int\n"
            )

    def test_allowed_datetime_in_date_field(self):
        """datetime is subclass of date; allowed values must reject
        datetime, same as bool is rejected for int."""
        with pytest.raises(ValueError, match="allowed.*type"):
            load_frontmatter_schema(
                "fields:\n"
                "  created:\n"
                "    type: date\n"
                "    allowed:\n"
                "      - 2026-03-04T12:00:00\n"
            )

    def test_duplicate_key_in_schema(self):
        """Duplicate keys in the schema YAML are rejected."""
        with pytest.raises(ValueError, match="duplicate"):
            load_frontmatter_schema(
                "fields:\n"
                "  title:\n"
                "    type: string\n"
                "  title:\n"
                "    type: int\n"
            )


# ============================================================
# validate — frontmatter validation against schema
# ============================================================


def _make_doc(frontmatter_yaml: str, body: str = "# Title\n") -> Document:
    """Helper: create a Document with frontmatter."""
    text = f"---\n{frontmatter_yaml}---\n{body}"
    doc = Document()
    doc.load(text=text)
    return doc


def _make_doc_no_frontmatter(body: str = "# Title\n") -> Document:
    """Helper: create a Document without frontmatter."""
    doc = Document()
    doc.load(text=body)
    return doc


def _schema(fields_yaml: str, extra: bool = False) -> str:
    """Helper: wrap field definitions in a schema string."""
    lines = fields_yaml.rstrip("\n").split("\n")
    indented = "\n".join(f"  {line}" for line in lines)
    return (
        f"allow_extra_fields: {str(extra).lower()}\n"
        f"fields:\n{indented}\n"
    )


# --- Happy paths ---


class TestValidateHappyPath:

    def test_all_required_fields_present(self):
        doc = _make_doc("title: Stormbringer\ndate: 2026-03-04\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\ndate:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_optional_field_absent(self):
        doc = _make_doc("title: Moonblade\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "draft:\n  type: bool\n  required: false\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_optional_field_present(self):
        doc = _make_doc("title: Moonblade\ndraft: true\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "draft:\n  type: bool\n  required: false\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_allowed_value_accepted(self):
        doc = _make_doc("status: draft\n")
        schema = load_frontmatter_schema(_schema(
            "status:\n  type: string\n  allowed:\n"
            "    - draft\n    - ready\n    - done\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_allowed_list_values_accepted(self):
        doc = _make_doc(
            "tactics:\n  - Recon\n  - Execution\n"
        )
        schema = load_frontmatter_schema(_schema(
            "tactics:\n  type: list\n  allowed:\n"
            "    - Recon\n    - Execution\n    - Impact\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_list_field_with_strings(self):
        doc = _make_doc(
            "contributors:\n  - Atreyu\n  - Bastian\n"
        )
        schema = load_frontmatter_schema(_schema(
            "contributors:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_int_field(self):
        doc = _make_doc("count: 42\n")
        schema = load_frontmatter_schema(_schema(
            "count:\n  type: int\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_float_field(self):
        doc = _make_doc("ratio: 3.14\n")
        schema = load_frontmatter_schema(_schema(
            "ratio:\n  type: float\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_bool_field(self):
        doc = _make_doc("draft: false\n")
        schema = load_frontmatter_schema(_schema(
            "draft:\n  type: bool\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_date_field(self):
        doc = _make_doc("created: 2026-03-04\n")
        schema = load_frontmatter_schema(_schema(
            "created:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_allow_extra_fields_with_unknown_field(self):
        doc = _make_doc("title: Stormbringer\nsurprise: hello\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n", extra=True
        ))
        results = validate(doc, schema)
        assert results == []

    def test_empty_schema_empty_frontmatter(self):
        doc = _make_doc_no_frontmatter()
        schema = load_frontmatter_schema("fields: {}\n")
        results = validate(doc, schema)
        assert results == []

    def test_all_optional_no_frontmatter(self):
        """Schema with only optional fields, document has no frontmatter."""
        doc = _make_doc_no_frontmatter()
        schema = load_frontmatter_schema(_schema(
            "draft:\n  type: bool\n  required: false\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_allowed_on_int_field(self):
        doc = _make_doc("level: 2\n")
        schema = load_frontmatter_schema(_schema(
            "level:\n  type: int\n  allowed:\n"
            "    - 1\n    - 2\n    - 3\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_allowed_on_bool_field(self):
        doc = _make_doc("flag: true\n")
        schema = load_frontmatter_schema(_schema(
            "flag:\n  type: bool\n  allowed:\n"
            "    - true\n"
        ))
        results = validate(doc, schema)
        assert results == []


# --- Missing field ---


class TestValidateMissingField:

    def test_required_field_missing(self):
        doc = _make_doc("date: 2026-03-04\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "date:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.missing_field"
        assert "title" in results[0].message

    def test_multiple_required_fields_missing(self):
        doc = _make_doc_no_frontmatter()
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "status:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 2
        rule_ids = {r.rule_id for r in results}
        assert rule_ids == {"schema.frontmatter.missing_field"}

    def test_required_field_missing_no_frontmatter(self):
        doc = _make_doc_no_frontmatter()
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.missing_field"


# --- Extra field ---


class TestValidateExtraField:

    def test_extra_field_rejected(self):
        doc = _make_doc("title: Stormbringer\nsurprise: boo\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.extra_field"
        assert "surprise" in results[0].message

    def test_multiple_extra_fields_rejected(self):
        doc = _make_doc(
            "title: X\nfoo: bar\nbaz: qux\n"
        )
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 2
        assert all(
            r.rule_id == "schema.frontmatter.extra_field"
            for r in results
        )

    def test_extra_field_allowed_when_flag_set(self):
        doc = _make_doc("title: X\nfoo: bar\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n", extra=True
        ))
        results = validate(doc, schema)
        assert results == []


# --- Wrong type ---


class TestValidateWrongType:

    def test_string_field_gets_int(self):
        doc = _make_doc("title: 42\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_int_field_gets_string(self):
        doc = _make_doc("count: not_a_number\n")
        schema = load_frontmatter_schema(_schema(
            "count:\n  type: int\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_int_field_gets_bool(self):
        """bool is subclass of int — must be explicitly rejected."""
        doc = _make_doc("count: true\n")
        schema = load_frontmatter_schema(_schema(
            "count:\n  type: int\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_bool_field_gets_string(self):
        doc = _make_doc("draft: not_a_bool\n")
        schema = load_frontmatter_schema(_schema(
            "draft:\n  type: bool\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_date_field_gets_string(self):
        doc = _make_doc("created: not-a-date\n")
        schema = load_frontmatter_schema(_schema(
            "created:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_list_field_gets_string(self):
        doc = _make_doc("tags: just_a_string\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_float_field_gets_string(self):
        doc = _make_doc("ratio: nope\n")
        schema = load_frontmatter_schema(_schema(
            "ratio:\n  type: float\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_string_field_gets_bool(self):
        doc = _make_doc("title: true\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_string_field_gets_date(self):
        doc = _make_doc("title: 2026-03-04\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_date_field_gets_datetime(self):
        """datetime is subclass of date — must be explicitly rejected,
        same as bool for int."""
        doc = _make_doc("created: 2026-03-04T12:00:00\n")
        schema = load_frontmatter_schema(_schema(
            "created:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"
        assert "datetime" in results[0].message


# --- Value not allowed ---


class TestValidateValueNotAllowed:

    def test_string_value_not_in_allowed(self):
        doc = _make_doc("status: archived\n")
        schema = load_frontmatter_schema(_schema(
            "status:\n  type: string\n  allowed:\n"
            "    - draft\n    - ready\n    - done\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.value_not_allowed"
        assert "archived" in results[0].message

    def test_int_value_not_in_allowed(self):
        doc = _make_doc("level: 99\n")
        schema = load_frontmatter_schema(_schema(
            "level:\n  type: int\n  allowed:\n"
            "    - 1\n    - 2\n    - 3\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.value_not_allowed"

    def test_list_item_not_in_allowed(self):
        doc = _make_doc(
            "tactics:\n  - Recon\n  - MadeUpTactic\n"
        )
        schema = load_frontmatter_schema(_schema(
            "tactics:\n  type: list\n  allowed:\n"
            "    - Recon\n    - Execution\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.value_not_allowed"
        assert "MadeUpTactic" in results[0].message

    def test_multiple_list_items_not_in_allowed(self):
        doc = _make_doc(
            "tactics:\n  - Bad1\n  - Bad2\n"
        )
        schema = load_frontmatter_schema(_schema(
            "tactics:\n  type: list\n  allowed:\n"
            "    - Recon\n    - Execution\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 2
        assert all(
            r.rule_id == "schema.frontmatter.value_not_allowed"
            for r in results
        )


# --- Duplicate list items ---


class TestValidateDuplicateListItem:

    def test_duplicate_items_rejected(self):
        doc = _make_doc(
            "tactics:\n  - Recon\n  - Recon\n"
        )
        schema = load_frontmatter_schema(_schema(
            "tactics:\n  type: list\n  allowed:\n"
            "    - Recon\n    - Execution\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.duplicate_list_item"
            for r in results
        )

    def test_duplicate_items_without_allowed(self):
        doc = _make_doc(
            "contributors:\n  - Falkor\n  - Falkor\n"
        )
        schema = load_frontmatter_schema(_schema(
            "contributors:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == \
            "schema.frontmatter.duplicate_list_item"
        assert "Falkor" in results[0].message

    def test_no_duplicates_passes(self):
        doc = _make_doc(
            "contributors:\n  - Atreyu\n  - Bastian\n"
        )
        schema = load_frontmatter_schema(_schema(
            "contributors:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert results == []


# --- Map not supported ---


class TestValidateMapNotSupported:

    def test_map_value_rejected(self):
        doc = _make_doc(
            "params:\n  key: value\n  other: thing\n"
        )
        schema = load_frontmatter_schema(_schema(
            "params:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.map_not_supported"
            for r in results
        )

    def test_map_value_rejected_regardless_of_declared_type(self):
        """Even if type is list, a map value is caught."""
        doc = _make_doc(
            "config:\n  nested:\n    deep: value\n"
        )
        schema = load_frontmatter_schema(_schema(
            "config:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.map_not_supported"
            for r in results
        )


# --- List item not string ---


class TestValidateListItemNotString:

    def test_int_item_in_list(self):
        doc = _make_doc("tags:\n  - 42\n  - hello\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.list_item_not_string"
            for r in results
        )

    def test_bool_item_in_list(self):
        doc = _make_doc("tags:\n  - true\n  - hello\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.list_item_not_string"
            for r in results
        )

    def test_nested_list_in_list(self):
        doc = Document()
        doc.load(text=(
            "---\n"
            "tags:\n"
            "  - - nested\n"
            "    - list\n"
            "---\n"
            "# Title\n"
        ))
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.list_item_not_string"
            for r in results
        )

    def test_map_item_in_list(self):
        doc = Document()
        doc.load(text=(
            "---\n"
            "tags:\n"
            "  - key: value\n"
            "---\n"
            "# Title\n"
        ))
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.list_item_not_string"
            for r in results
        )


# --- Duplicate YAML key in frontmatter ---


class TestValidateDuplicateKey:

    def test_duplicate_key_in_frontmatter(self):
        doc = Document()
        doc.load(text=(
            "---\n"
            "title: First\n"
            "title: Second\n"
            "---\n"
            "# Heading\n"
        ))
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.duplicate_key"
            for r in results
        )


# --- Position reporting ---


class TestValidatePositionReporting:

    def test_error_position_points_to_frontmatter(self):
        doc = _make_doc("date: 2026-03-04\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "date:\n  type: date\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].position == doc.frontmatter.position

    def test_no_frontmatter_position_is_zero(self):
        doc = _make_doc_no_frontmatter()
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].position.offset == 0
        assert results[0].position.length == 0


# --- Combined error scenarios ---


class TestValidateCombined:

    def test_missing_and_extra_and_wrong_type(self):
        """Multiple error types in one validation pass."""
        doc = _make_doc(
            "surprise: boo\ncount: not_an_int\n"
        )
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
            "count:\n  type: int\n"
        ))
        results = validate(doc, schema)
        rule_ids = {r.rule_id for r in results}
        assert "schema.frontmatter.missing_field" in rule_ids
        assert "schema.frontmatter.extra_field" in rule_ids
        assert "schema.frontmatter.wrong_type" in rule_ids

    def test_wrong_type_skips_allowed_check(self):
        """If type is wrong, don't also report value_not_allowed."""
        doc = _make_doc("status: 42\n")
        schema = load_frontmatter_schema(_schema(
            "status:\n  type: string\n  allowed:\n"
            "    - draft\n    - ready\n"
        ))
        results = validate(doc, schema)
        rule_ids = [r.rule_id for r in results]
        assert "schema.frontmatter.wrong_type" in rule_ids
        assert "schema.frontmatter.value_not_allowed" not in rule_ids

    def test_list_type_wrong_skips_item_checks(self):
        """If field isn't a list, don't check items."""
        doc = _make_doc("tags: not_a_list\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n  allowed:\n"
            "    - a\n    - b\n"
        ))
        results = validate(doc, schema)
        rule_ids = [r.rule_id for r in results]
        assert "schema.frontmatter.wrong_type" in rule_ids
        assert "schema.frontmatter.value_not_allowed" not in rule_ids
        assert "schema.frontmatter.list_item_not_string" not in rule_ids
        assert "schema.frontmatter.duplicate_list_item" not in rule_ids


# --- Edge cases ---


class TestValidateEdgeCases:

    def test_empty_list_passes(self):
        doc = _make_doc("tags: []\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_empty_string_value(self):
        doc = _make_doc("title: ''\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_non_ascii_string_value(self):
        doc = _make_doc("title: 'Ünïcödé 🎉'\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_non_ascii_in_allowed_list(self):
        doc = _make_doc("région: Île-de-France\n")
        schema = load_frontmatter_schema(_schema(
            "région:\n  type: string\n  allowed:\n"
            "    - Île-de-France\n    - Bretagne\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_null_field_value_wrong_type(self):
        """YAML `null` / `~` is parsed as None — always a type error."""
        doc = _make_doc("title:\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_int_rejected_for_float_field(self):
        """YAML parses 1.0 as float but 1 as int — int must be
        rejected when the schema declares float."""
        doc = _make_doc("ratio: 1\n")
        schema = load_frontmatter_schema(_schema(
            "ratio:\n  type: float\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.wrong_type"

    def test_single_item_list(self):
        doc = _make_doc("tags:\n  - solo\n")
        schema = load_frontmatter_schema(_schema(
            "tags:\n  type: list\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_frontmatter_with_only_extra_fields_strict(self):
        doc = _make_doc("rogue: field\n")
        schema = load_frontmatter_schema("fields: {}\n")
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.extra_field"

    def test_frontmatter_with_only_extra_fields_permissive(self):
        doc = _make_doc("rogue: field\n")
        schema = load_frontmatter_schema(
            "allow_extra_fields: true\nfields: {}\n"
        )
        results = validate(doc, schema)
        assert results == []

    def test_empty_frontmatter_block_with_required_field(self):
        """Frontmatter block exists but is empty (---\\n\\n---\\n).
        FrontMatter.content is None in this case."""
        doc = Document()
        doc.load(text="---\n\n---\n# Title\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert len(results) == 1
        assert results[0].rule_id == "schema.frontmatter.missing_field"

    def test_empty_frontmatter_block_all_optional(self):
        """Empty frontmatter with only optional fields passes."""
        doc = Document()
        doc.load(text="---\n\n---\n# Title\n")
        schema = load_frontmatter_schema(_schema(
            "draft:\n  type: bool\n  required: false\n"
        ))
        results = validate(doc, schema)
        assert results == []

    def test_scalar_frontmatter_rejected(self):
        """Frontmatter that is a bare scalar (not a mapping) is
        caught with a clear error instead of crashing."""
        doc = Document()
        doc.load(text="---\n42\n---\n# Title\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.wrong_type"
            and "mapping" in r.message
            for r in results
        )
        # Required field should also be reported as missing
        assert any(
            r.rule_id == "schema.frontmatter.missing_field"
            for r in results
        )

    def test_list_frontmatter_rejected(self):
        """Frontmatter that is a bare list (not a mapping) is caught."""
        doc = Document()
        doc.load(text="---\n- one\n- two\n---\n# Title\n")
        schema = load_frontmatter_schema(_schema(
            "title:\n  type: string\n"
        ))
        results = validate(doc, schema)
        assert any(
            r.rule_id == "schema.frontmatter.wrong_type"
            and "mapping" in r.message
            for r in results
        )
