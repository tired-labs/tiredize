# Standard library
from __future__ import annotations
from pathlib import Path
from typing import Any

# Third-party
import requests

# Local
from tiredize.markdown.types.document import Document


def get_config_int(
    config: dict[str, Any],
    key: str
) -> int | None:
    """
    Retrieve an integer configuration value.
    """
    raw_value = config.get(key)
    if isinstance(raw_value, bool) or not isinstance(raw_value, int):
        return None
    return raw_value


def get_config_str(
    config: dict[str, Any],
    key: str
) -> str | None:
    """
    Retrieve an string configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, str):
        return None
    return raw_value


def get_config_bool(
    config: dict[str, Any],
    key: str
) -> bool | None:
    """
    Retrieve a boolean configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, bool):
        return None
    return raw_value


def get_config_dict(
    config: dict[str, Any],
    key: str
) -> dict[str, Any] | None:
    """
    Retrieve a dictionary configuration value.
    """
    raw_value: dict[str, Any] | None = config.get(key)
    if not isinstance(raw_value, dict):
        return None
    return raw_value


def get_config_list(
    config: dict[str, Any],
    key: str
) -> list[str] | None:
    """
    Retrieve a list configuration value.
    """
    raw_value: list[str] | None = config.get(key)
    if not isinstance(raw_value, list):
        return None
    return raw_value


def _matches_status(code: int, patterns: list[int | str]) -> bool:
    for p in patterns:
        if isinstance(p, int) and code == p:
            return True
        if isinstance(p, str) and code // 100 == int(p[0]):
            return True
    return False


def check_url_valid(
    document: Document,
    url: str,
    timeout: float | None = None,
    headers: dict[str, Any] | None = None,
    allow_redirects: bool | None = None,
    verify_ssl: bool | None = None,
    valid_status_codes: list[int | str] | None = None,
) -> tuple[bool, int | None, str | None]:
    """
    Perform a lightweight check to determine if a URL is reachable.

    Returns a tuple:
        (is_valid, status_code, error_message)

    is_valid:
        True if the response status code is considered valid. By default,
        2xx and 3xx codes are valid. Pass valid_status_codes to override.
    status_code:
        The HTTP response code if one was returned. Otherwise None.
    error_message:
        A string describing any failure such as timeout or connection error.

    This helper does not raise exceptions. All failures are returned
    in the tuple so callers do not need try/except logic.
    """
    if url.startswith("#"):
        for section in document.sections:
            if section.header.slug == url:
                return True, None, None
        return False, None, "anchor not found in document"

    if url.startswith("."):
        if document.path is None:
            return False, None, "document has no path for relative URL"

        path = document.path.parent / Path(url)
        if path.exists():
            return True, None, None
        else:
            return False, None, "relative file not found"

    req_headers = headers or {
        "User-Agent": "tiredize-link-checker/1.0"
    }

    try:
        if allow_redirects is None:
            allow_redirects = True

        response = requests.get(
            url=url,
            headers=req_headers,
            timeout=timeout,
            allow_redirects=allow_redirects,
            verify=verify_ssl,
        )
        if valid_status_codes is not None:
            is_valid = _matches_status(response.status_code, valid_status_codes)
        else:
            is_valid = 200 <= response.status_code < 400
        return is_valid, response.status_code, None

    except requests.exceptions.Timeout:
        return False, None, "timeout"

    # Covers DNS errors, connection failures,
    # SSL issues, invalid URLs, etc.
    except requests.exceptions.RequestException as exc:
        return False, None, str(exc)
