import textwrap
from tiredize.document import Document
from tiredize.validators.front_matter import validate_front_matter


def make_doc(md: str) -> Document:
    md = textwrap.dedent(md).lstrip("\n")
    return Document.from_text(md)


FRONT_MATTER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Test front matter schema",
    "type": "object",
    "required": ["id", "title", "status"],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "pattern": "^TRR\\d{4}$"},
        "title": {"type": "string", "minLength": 3},
        "status": {"type": "string", "enum": ["draft", "review", "published"]},
    },
}


def schema_cfg():
    return {"front_matter": {"schema": FRONT_MATTER_SCHEMA}}


def test_front_matter_valid_passes():
    md = """
    ---
    id: TRR0001
    title: Example TRR
    status: draft
    ---
    # Title
    """

    doc = make_doc(md)
    results = validate_front_matter(doc, schema_cfg())

    assert results == [], "Expected no validation errors for valid"
    "front matter"


def test_front_matter_missing_required_fields():
    md = """
    ---
    id: TRR0001
    ---
    # Title
    """

    doc = make_doc(md)
    results = validate_front_matter(doc, schema_cfg())

    assert len(results) == 2, "Expected exactly two missing-field errors"

    # Missing: title
    title_errors = [
        r for r in results
        if r.message.startswith("<root>:")
        and "title" in r.message and "required property" in r.message
    ]
    assert len(title_errors) == 1, "Expected a single missing 'title' error"

    # Missing: status
    status_errors = [
        r for r in results
        if r.message.startswith("<root>:")
        and "status" in r.message and "required property" in r.message
    ]
    assert len(status_errors) == 1, "Expected a single missing 'status' error"


def test_front_matter_pattern_and_enum_violations():
    md = """
    ---
    id: BAD1234
    title: Ex
    status: invalid_status
    extra_field: not allowed
    ---
    # Title
    """

    doc = make_doc(md)
    results = validate_front_matter(doc, schema_cfg())

    assert len(results) == 4, "Expected exactly four validation errors"

    # id pattern violation
    id_pattern_errors = [
        r for r in results
        if r.message.startswith("id:") and "does not match" in r.message
    ]
    assert len(id_pattern_errors) == 1, "Expected one pattern violation"
    "for 'id'"

    # title too short
    title_length_errors = [
        r for r in results
        if r.message.startswith("title:") and "is too short" in r.message
    ]
    assert len(title_length_errors) == 1, "Expected one 'title' "
    "minLength violation"

    # status enum violation
    status_enum_errors = [
        r for r in results
        if r.message.startswith("status:") and "is not one of" in r.message
    ]
    assert len(status_enum_errors) == 1, "Expected one enum violation"
    "for 'status'"

    # additionalProperties false
    extra_field_errors = [
        r for r in results
        if r.message.startswith("<root>:") and "extra_field" in r.message
    ]
    assert len(extra_field_errors) == 1, "Expected one additionalProperties"
    "violation"
