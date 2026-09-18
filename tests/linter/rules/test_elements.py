"""Tests for tiredize/linter/rules/elements.py."""

import copy

import pytest

from tiredize.linter.rules.elements import validate
from tiredize.markdown.types.document import Document


# ===================================================================
#  Config gating
# ===================================================================


def test_empty_disallow_returns_empty():
    """An empty disallow list produces no violations."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    results = validate(doc, {"disallow": []})
    assert results == []


def test_unknown_element_name_raises():
    """An unknown element name in disallow raises ValueError."""
    doc = Document()
    doc.load(text="# H\n")
    with pytest.raises(ValueError, match="bad_element"):
        validate(doc, {"disallow": ["bad_element"]})


# ===================================================================
#  Configuration validation (key level)
#
#  `disallow` is required: without it the rule inspects nothing, so
#  enabling `elements` would be a no-op. See "Validating rule
#  configuration" in .context/issues/main-module-exit-code.md.
# ===================================================================


def test_missing_disallow_raises():
    """Enabling the rule without `disallow` would check nothing."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {})
    message = str(excinfo.value)
    assert "elements" in message
    assert "disallow" in message


def test_unknown_key_raises():
    """A key the rule does not accept is an error."""
    doc = Document()
    doc.load(text="# H\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {"disallow": [], "snooze_button": True})
    message = str(excinfo.value)
    assert "elements" in message
    assert "snooze_button" in message


def test_disallow_wrong_type_raises():
    """`disallow` wants a list, not a bare string."""
    doc = Document()
    doc.load(text="# H\n")
    with pytest.raises(ValueError, match="disallow"):
        validate(doc, {"disallow": "table"})


def test_unknown_key_reported_before_bad_element_name():
    """Key-level validation runs before the value-level check."""
    doc = Document()
    doc.load(text="# H\n")
    with pytest.raises(ValueError) as excinfo:
        validate(
            doc,
            {"disallow": ["bad_element"], "snooze_button": True},
        )
    assert "snooze_button" in str(excinfo.value)


# ===================================================================
#  Single element type
# ===================================================================


def test_disallow_link_inline_present():
    """Disallowing 'link_inline' flags each inline link found."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    results = validate(doc, {"disallow": ["link_inline"]})
    assert len(results) == 1
    assert "Inline link" in results[0].message


def test_disallow_link_inline_absent():
    """No violation when the disallowed element is absent from the document."""
    doc = Document()
    doc.load(text="# H\nPlain text only.\n")
    results = validate(doc, {"disallow": ["link_inline"]})
    assert results == []


def test_disallow_table():
    """Disallowing 'table' flags each table found."""
    doc = Document()
    doc.load(text="# H\n| a | b |\n| --- | --- |\n| 1 | 2 |\n")
    results = validate(doc, {"disallow": ["table"]})
    assert len(results) == 1
    assert "Table" in results[0].message


def test_disallow_code_block():
    """Disallowing 'code_block' flags each fenced code block."""
    doc = Document()
    doc.load(text="# H\n```python\nprint('hi')\n```\n")
    results = validate(doc, {"disallow": ["code_block"]})
    assert len(results) == 1
    assert "Fenced code block" in results[0].message


def test_disallow_link_bare():
    """Disallowing 'link_bare' flags bare URLs."""
    doc = Document()
    doc.load(text="# H\nhttps://example.com\n")
    results = validate(doc, {"disallow": ["link_bare"]})
    assert len(results) == 1
    assert "Bare link" in results[0].message


def test_disallow_quoteblock():
    """Disallowing 'quoteblock' flags blockquotes."""
    doc = Document()
    doc.load(text="# H\n> This is a quote.\n")
    results = validate(doc, {"disallow": ["quoteblock"]})
    assert len(results) == 1
    assert "Blockquote" in results[0].message


# ===================================================================
#  Multiple occurrences and types
# ===================================================================


def test_multiple_occurrences_each_flagged():
    """Each occurrence of a disallowed element produces a separate
    violation."""
    doc = Document()
    doc.load(text=(
        "# H\n[a](https://example.com) and [b](https://example.org)\n"
    ))
    results = validate(doc, {"disallow": ["link_inline"]})
    assert len(results) == 2


def test_disallow_multiple_types():
    """Violations are reported for each disallowed type present."""
    doc = Document()
    doc.load(text=(
        "# H\n[click](https://example.com)\n| a | b |\n| --- | --- |\n"
    ))
    results = validate(doc, {"disallow": ["link_inline", "table"]})
    assert len(results) == 2
    messages = {r.message for r in results}
    assert any("Inline link" in m for m in messages)
    assert any("Table" in m for m in messages)


def test_disallow_across_multiple_sections():
    """Violations are collected from all sections, not just the first."""
    md = (
        "# Section One\n"
        "[a](https://example.com)\n"
        "# Section Two\n"
        "[b](https://example.org)\n"
    )
    doc = Document()
    doc.load(text=md)
    results = validate(doc, {"disallow": ["link_inline"]})
    assert len(results) == 2


# ===================================================================
#  Position and rule_id
# ===================================================================


def test_violation_position_matches_element():
    """The violation position matches the element's position in the
    document."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    results = validate(doc, {"disallow": ["link_inline"]})
    assert len(results) == 1
    assert results[0].position.offset == 4
    assert results[0].position.length > 0


def test_rule_id_is_none():
    """validate() returns results with rule_id=None (engine fills it in)."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    results = validate(doc, {"disallow": ["link_inline"]})
    assert all(r.rule_id is None for r in results)


# ===================================================================
#  State mutation
# ===================================================================


def test_does_not_mutate_document():
    """validate() must not change the Document."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    original_string = doc.string
    validate(doc, {"disallow": ["link_inline"]})
    assert doc.string == original_string


def test_does_not_mutate_config():
    """validate() must not change the config dict."""
    doc = Document()
    doc.load(text="# H\n[click](https://example.com)\n")
    config = {"disallow": ["link_inline"]}
    config_copy = copy.deepcopy(config)
    validate(doc, config)
    assert config == config_copy


def test_non_string_disallow_entry_still_raises_value_level_error():
    """Key-level validation does not swallow the value-level check."""
    doc = Document()
    doc.load(text="# H\n")
    with pytest.raises(ValueError, match="entries must be strings"):
        validate(doc, {"disallow": [42]})


# ===================================================================
#  Acceptance tests: autolink-gfm-parity (step 2, before implementation)
#
#  The element vocabulary takes the specification's names: `autolink`
#  (was `link_bracket`) and `autolink_extended` (was `link_bare`).
#  Findings are labelled "Autolink" and "Extended autolink". The old
#  names are rejected with the existing unknown-element error; no
#  alias is kept. Autolinks of any scheme count as elements, even
#  though the `links` rule validates only http and https.
# ===================================================================


PENDING = "autolink-gfm-parity: awaiting implementation (step 3)"


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize(
    "markdown",
    ["<https://moonbase.example>", "<irc://foo.bar:2233/baz>",
     "<foo@bar.example.com>"],
    ids=["https", "irc", "email"],
)
def test_disallow_autolink_flags_each_scheme(markdown):
    doc = Document()
    doc.load(text=f"# H\n{markdown}\n")
    results = validate(doc, {"disallow": ["autolink"]})
    assert len(results) == 1
    assert "Autolink" in results[0].message
    assert "Extended" not in results[0].message


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize(
    "markdown",
    ["https://moonbase.example", "www.moonbase.example",
     "foo@bar.baz", "mailto:foo@bar.baz"],
    ids=["https", "www", "email", "mailto"],
)
def test_disallow_autolink_extended_flags_each_form(markdown):
    doc = Document()
    doc.load(text=f"# H\nContact {markdown} for details.\n")
    results = validate(doc, {"disallow": ["autolink_extended"]})
    assert len(results) == 1
    assert "Extended autolink" in results[0].message


@pytest.mark.skip(reason=PENDING)
def test_disallow_autolink_does_not_flag_extended_autolink():
    """The two vocabularies are distinct: a bare URL is not an
    `autolink`, and a bracketed one is not an `autolink_extended`."""
    doc = Document()
    doc.load(text="# H\nhttps://moonbase.example\n<https://x.example>\n")
    assert len(validate(doc, {"disallow": ["autolink"]})) == 1
    assert len(validate(doc, {"disallow": ["autolink_extended"]})) == 1


@pytest.mark.skip(reason=PENDING)
@pytest.mark.parametrize("old_name", ["link_bare", "link_bracket"])
def test_disallow_rejects_old_link_names(old_name):
    doc = Document()
    doc.load(text="# H\nhttps://moonbase.example\n")
    with pytest.raises(ValueError) as excinfo:
        validate(doc, {"disallow": [old_name]})
    assert str(excinfo.value) == (
        f"Unknown element name in disallow: '{old_name}'"
    )
