"""Tests for tiredize/linter/utils.py.

Covers config helpers (get_config_*), check_url_valid for relative URLs,
anchors, and HTTP paths. HTTP tests mock requests.get to avoid network
calls.
"""

# Standard library
from __future__ import annotations
import copy
from unittest.mock import MagicMock
from unittest.mock import patch

# Third-party
import pytest
import requests

# Local
from tiredize.linter.utils import check_url_valid
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import get_config_dict
from tiredize.linter.utils import get_config_int
from tiredize.linter.utils import get_config_list
from tiredize.linter.utils import get_config_str
from tiredize.markdown.types.document import Document


# ===================================================================
#  get_config_int
# ===================================================================


def test_get_config_int_correct_type():
    """Returns the integer when the value is an int."""
    assert get_config_int({"lives": 3}, "lives") == 3


def test_get_config_int_wrong_type():
    """Returns None when the value is not an int."""
    assert get_config_int({"lives": "three"}, "lives") is None


def test_get_config_int_missing_key():
    """Returns None when the key is absent."""
    assert get_config_int({}, "lives") is None


@pytest.mark.skip(
    reason="get_config_int accepts bool because isinstance(True, int) "
    "is True in Python. See issue fix-config-int-bool-guard.md"
)
def test_get_config_int_bool_returns_none():
    """bool is a subclass of int and should be rejected.

    A bool config value is semantically different from an integer.
    get_config_int should return None for bool inputs.
    """
    assert get_config_int({"flag": True}, "flag") is None


def test_get_config_int_does_not_mutate_config():
    """Config dict is unchanged after the call."""
    config = {"hp": 100}
    original = copy.deepcopy(config)
    get_config_int(config, "hp")
    assert config == original


# ===================================================================
#  get_config_str
# ===================================================================


def test_get_config_str_correct_type():
    """Returns the string when the value is a str."""
    assert get_config_str({"name": "Gandalf"}, "name") == "Gandalf"


def test_get_config_str_wrong_type():
    """Returns None when the value is not a str."""
    assert get_config_str({"name": 42}, "name") is None


def test_get_config_str_missing_key():
    """Returns None when the key is absent."""
    assert get_config_str({}, "name") is None


def test_get_config_str_does_not_mutate_config():
    """Config dict is unchanged after the call."""
    config = {"title": "wizard"}
    original = copy.deepcopy(config)
    get_config_str(config, "title")
    assert config == original


# ===================================================================
#  get_config_bool
# ===================================================================


def test_get_config_bool_correct_type_true():
    """Returns True when the value is True."""
    assert get_config_bool({"stealth": True}, "stealth") is True


def test_get_config_bool_correct_type_false():
    """Returns False when the value is False."""
    assert get_config_bool({"stealth": False}, "stealth") is False


def test_get_config_bool_wrong_type():
    """Returns None when the value is not a bool."""
    assert get_config_bool({"stealth": "yes"}, "stealth") is None


def test_get_config_bool_missing_key():
    """Returns None when the key is absent."""
    assert get_config_bool({}, "stealth") is None


def test_get_config_bool_does_not_mutate_config():
    """Config dict is unchanged after the call."""
    config = {"enabled": True}
    original = copy.deepcopy(config)
    get_config_bool(config, "enabled")
    assert config == original


# ===================================================================
#  get_config_dict
# ===================================================================


def test_get_config_dict_correct_type():
    """Returns the dict when the value is a dict."""
    headers = {"User-Agent": "sphinx"}
    assert get_config_dict({"headers": headers}, "headers") == headers


def test_get_config_dict_wrong_type():
    """Returns None when the value is not a dict."""
    assert get_config_dict({"headers": "nope"}, "headers") is None


def test_get_config_dict_missing_key():
    """Returns None when the key is absent."""
    assert get_config_dict({}, "headers") is None


def test_get_config_dict_does_not_mutate_config():
    """Config dict is unchanged after the call."""
    config = {"meta": {"a": 1}}
    original = copy.deepcopy(config)
    get_config_dict(config, "meta")
    assert config == original


# ===================================================================
#  get_config_list
# ===================================================================


def test_get_config_list_correct_type():
    """Returns the list when the value is a list."""
    assert get_config_list({"tags": ["a", "b"]}, "tags") == ["a", "b"]


def test_get_config_list_wrong_type():
    """Returns None when the value is not a list."""
    assert get_config_list({"tags": "a,b"}, "tags") is None


def test_get_config_list_missing_key():
    """Returns None when the key is absent."""
    assert get_config_list({}, "tags") is None


def test_get_config_list_does_not_mutate_config():
    """Config dict is unchanged after the call."""
    config = {"items": [1, 2]}
    original = copy.deepcopy(config)
    get_config_list(config, "items")
    assert config == original


# ===================================================================
#  check_url_valid: relative URLs (from fix-relative-url-resolution)
# ===================================================================


def test_relative_url_resolves_to_parent_directory(tmp_path):
    """./sibling.md should resolve relative to the document's directory,
    not relative to the document file path itself."""
    doc_file = tmp_path / "reports" / "dragon-sighting.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("# Dragon Sighting")

    sibling = tmp_path / "reports" / "treasure-map.md"
    sibling.write_text("# Treasure Map")

    doc = Document()
    doc.path = doc_file

    is_valid, status, error = check_url_valid(doc, "./treasure-map.md")
    assert is_valid is True
    assert error is None


def test_relative_url_file_not_found(tmp_path):
    doc_file = tmp_path / "lonely-wizard.md"
    doc_file.write_text("# Lonely Wizard")

    doc = Document()
    doc.path = doc_file

    is_valid, status, error = check_url_valid(
        doc, "./nonexistent-spell.md"
    )
    assert is_valid is False
    assert error == "relative file not found"


def test_relative_url_no_document_path():
    doc = Document()
    doc.path = None

    is_valid, status, error = check_url_valid(doc, "./ghost-file.md")
    assert is_valid is False
    assert "no path" in error


# ===================================================================
#  check_url_valid: anchor path
# ===================================================================


def test_anchor_found_in_document():
    """Anchor matching an existing section slug returns success."""
    doc = Document()
    doc.load(text="# Potions\n\nBrew stuff.\n")
    # The slug for "Potions" should be "#potions"
    is_valid, status, error = check_url_valid(doc, "#potions")
    assert is_valid is True
    assert status is None
    assert error is None


def test_anchor_not_found():
    """Anchor not matching any section slug returns failure."""
    doc = Document()
    doc.load(text="# Potions\n\nBrew stuff.\n")
    is_valid, status, error = check_url_valid(doc, "#dragons")
    assert is_valid is False
    assert status is None
    assert error == "anchor not found in document"


def test_anchor_document_with_no_sections():
    """A document parsed with no sections still returns not found."""
    doc = Document()
    doc.sections = []
    is_valid, status, error = check_url_valid(doc, "#anywhere")
    assert is_valid is False
    assert error == "anchor not found in document"


# ===================================================================
#  check_url_valid: anchor -- unicode (audit point 9)
# ===================================================================


@pytest.mark.skip(
    reason="slugify_header strips non-ASCII via [^a-z0-9 \\-] regex. "
    "GFM preserves non-ASCII in slugs. "
    "See issue fix-slug-non-ascii.md"
)
def test_anchor_with_non_ascii_slug():
    """Anchor with non-ASCII characters should match per GFM rules.

    GFM preserves non-ASCII in slugs: "Café Section" should produce
    "#café-section", not "#caf-section".
    """
    doc = Document()
    doc.load(text="# Caf\u00e9 Section\n\nContent.\n")
    assert doc.sections[0].header.slug == "#caf\u00e9-section"

    is_valid, _, _ = check_url_valid(doc, "#caf\u00e9-section")
    assert is_valid is True


# ===================================================================
#  check_url_valid: relative URL -- unicode (audit point 9)
# ===================================================================


def test_relative_url_with_non_ascii_filename(tmp_path):
    """Relative path with non-ASCII filename resolves correctly."""
    doc_file = tmp_path / "index.md"
    doc_file.write_text("# Index")
    sibling = tmp_path / "caf\u00e9.md"
    sibling.write_text("# Caf\u00e9")

    doc = Document()
    doc.path = doc_file

    is_valid, status, error = check_url_valid(
        doc, "./caf\u00e9.md"
    )
    assert is_valid is True
    assert error is None


# ===================================================================
#  check_url_valid: HTTP path (mocked)
# ===================================================================


MOCK_TARGET = "tiredize.linter.utils.requests.get"


def _make_mock_response(status_code):
    """Create a mock response with the given status code."""
    resp = MagicMock()
    resp.status_code = status_code
    return resp


def test_http_200_success():
    """2xx response returns (True, status_code, None)."""
    doc = Document()
    with patch(MOCK_TARGET, return_value=_make_mock_response(200)):
        is_valid, status, error = check_url_valid(
            doc, "https://example.com"
        )
    assert is_valid is True
    assert status == 200
    assert error is None


def test_http_301_redirect():
    """3xx response returns (True, status_code, None)."""
    doc = Document()
    with patch(MOCK_TARGET, return_value=_make_mock_response(301)):
        is_valid, status, error = check_url_valid(
            doc, "https://example.com/old"
        )
    assert is_valid is True
    assert status == 301
    assert error is None


def test_http_404_client_error():
    """4xx response returns (False, status_code, None)."""
    doc = Document()
    with patch(MOCK_TARGET, return_value=_make_mock_response(404)):
        is_valid, status, error = check_url_valid(
            doc, "https://example.com/missing"
        )
    assert is_valid is False
    assert status == 404
    assert error is None


def test_http_500_server_error():
    """5xx response returns (False, status_code, None)."""
    doc = Document()
    with patch(MOCK_TARGET, return_value=_make_mock_response(500)):
        is_valid, status, error = check_url_valid(
            doc, "https://example.com/broken"
        )
    assert is_valid is False
    assert status == 500
    assert error is None


def test_http_timeout():
    """Timeout returns (False, None, 'timeout')."""
    doc = Document()
    with patch(
        MOCK_TARGET,
        side_effect=requests.exceptions.Timeout("timed out")
    ):
        is_valid, status, error = check_url_valid(
            doc, "https://example.com/slow"
        )
    assert is_valid is False
    assert status is None
    assert error == "timeout"


def test_http_connection_error():
    """ConnectionError returns (False, None, error_string)."""
    doc = Document()
    with patch(
        MOCK_TARGET,
        side_effect=requests.exceptions.ConnectionError("DNS failed")
    ):
        is_valid, status, error = check_url_valid(
            doc, "https://no-such-host.example"
        )
    assert is_valid is False
    assert status is None
    assert "DNS failed" in error


def test_http_custom_headers_passed():
    """Custom headers are forwarded to requests.get."""
    doc = Document()
    custom = {"Authorization": "Bearer magic-token"}
    with patch(
        MOCK_TARGET, return_value=_make_mock_response(200)
    ) as mock_get:
        check_url_valid(
            doc, "https://example.com", headers=custom
        )
    _, kwargs = mock_get.call_args
    assert kwargs["headers"] == custom


def test_http_default_headers_when_none():
    """Default User-Agent header is used when headers is None."""
    doc = Document()
    with patch(
        MOCK_TARGET, return_value=_make_mock_response(200)
    ) as mock_get:
        check_url_valid(doc, "https://example.com")
    _, kwargs = mock_get.call_args
    assert "User-Agent" in kwargs["headers"]
    assert "tiredize" in kwargs["headers"]["User-Agent"]


def test_http_custom_timeout_passed():
    """Custom timeout is forwarded to requests.get."""
    doc = Document()
    with patch(
        MOCK_TARGET, return_value=_make_mock_response(200)
    ) as mock_get:
        check_url_valid(
            doc, "https://example.com", timeout=7
        )
    _, kwargs = mock_get.call_args
    assert kwargs["timeout"] == 7


def test_http_verify_ssl_passed():
    """Custom verify_ssl is forwarded to requests.get as verify."""
    doc = Document()
    with patch(
        MOCK_TARGET, return_value=_make_mock_response(200)
    ) as mock_get:
        check_url_valid(
            doc, "https://example.com", verify_ssl=False
        )
    _, kwargs = mock_get.call_args
    assert kwargs["verify"] is False


def test_http_allow_redirects_defaults_to_true():
    """When allow_redirects is None, it defaults to True."""
    doc = Document()
    with patch(
        MOCK_TARGET, return_value=_make_mock_response(200)
    ) as mock_get:
        check_url_valid(doc, "https://example.com")
    _, kwargs = mock_get.call_args
    assert kwargs["allow_redirects"] is True


# ===================================================================
#  check_url_valid: state mutation (audit point 8)
# ===================================================================


def test_check_url_valid_does_not_mutate_document_anchor():
    """Document is unchanged after anchor check."""
    doc = Document()
    doc.load(text="# Guard\n\nContent.\n")
    original_string = doc.string
    original_sections = len(doc.sections)
    check_url_valid(doc, "#guard")
    assert doc.string == original_string
    assert len(doc.sections) == original_sections


def test_check_url_valid_does_not_mutate_document_http():
    """Document is unchanged after HTTP check."""
    doc = Document()
    doc.load(text="# Safe\n\nContent.\n")
    original_string = doc.string
    with patch(MOCK_TARGET, return_value=_make_mock_response(200)):
        check_url_valid(doc, "https://example.com")
    assert doc.string == original_string
