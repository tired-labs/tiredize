from pathlib import Path
from tiredize.markdown.types.document import Document
import requests
import typing


def get_config_int(
    config: typing.Dict[str, typing.Any],
    key: str
) -> int | None:
    """
    Retrieve an integer configuration value.
    """
    raw_value = config.get(key)
    if not isinstance(raw_value, int):
        return None
    return raw_value


def get_config_str(
    config: typing.Dict[str, typing.Any],
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
    config: typing.Dict[str, typing.Any],
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
    config: typing.Dict[str, typing.Any],
    key: str
) -> typing.Dict[str, typing.Any] | None:
    """
    Retrieve a dictionary configuration value.
    """
    raw_value: dict[str, typing.Any] | None = config.get(key)
    if not isinstance(raw_value, dict):
        return None
    return raw_value


def get_config_list(
    config: typing.Dict[str, typing.Any],
    key: str
) -> typing.List[str] | None:
    """
    Retrieve a list configuration value.
    """
    raw_value: list[str] | None = config.get(key)
    if not isinstance(raw_value, list):
        return None
    return raw_value


def check_url_valid(
    document: Document,
    url: str,
    timeout: float | None = None,
    headers: typing.Optional[typing.Dict[str, typing.Any]] | None = None,
    allow_redirects: bool | None = None,
    verify_ssl: bool | None = None
) -> tuple[bool, int | None, str | None]:
    """
    Perform a lightweight check to determine if a URL is reachable.

    Returns a tuple:
        (is_valid, status_code, error_message)

    is_valid:
        True if the request completed with a 2xx or 3xx status code.
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

        path = document.path / Path(url)
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
        # Treat 2xx and 3xx as valid. You can change this policy later.
        if 200 <= response.status_code < 400:
            return True, response.status_code, None
        return False, response.status_code, None

    except requests.exceptions.Timeout:
        return False, None, "timeout"

    # Covers DNS errors, connection failures, SSL issues, invalid URLs, etc.
    except requests.exceptions.RequestException as exc:
        return False, None, str(exc)
