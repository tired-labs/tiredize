# Standard library
from __future__ import annotations
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from typing import Callable

# Third-party
import requests

# Local
from tiredize.markdown.types.document import Document


# The type vocabulary rule modules use to declare their accepted
# configuration keys. Each predicate mirrors the matching
# get_config_* accessor below, so a value validate_config accepts is
# a value that accessor will return rather than treat as absent.
_CONFIG_TYPE_CHECKS: dict[str, Callable[[Any], bool]] = {
    "bool": lambda value: isinstance(value, bool),
    "dict": lambda value: isinstance(value, dict),
    "int": (
        lambda value: isinstance(value, int)
        and not isinstance(value, bool)
    ),
    "list": lambda value: isinstance(value, list),
    "str": lambda value: isinstance(value, str),
}

# Human-readable names for the same vocabulary, for error messages.
_CONFIG_TYPE_LABELS: dict[str, str] = {
    "bool": "a boolean",
    "dict": "a mapping",
    "int": "an integer",
    "list": "a list",
    "str": "a string",
}


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


def validate_config(
    config: dict[str, Any],
    allowed: dict[str, str],
    required: Iterable[str],
    rule_id: str,
) -> None:
    """
    Validate a rule's configuration block before the rule reads it.

    Every built-in rule calls this as the first thing its validate()
    does, passing the keys it accepts and the subset it requires.
    Three states are errors, each raising ValueError naming the rule
    id and the offending key:

    - a key the rule does not accept,
    - a key the rule accepts holding a value of the wrong type,
    - a required key that was omitted.

    An omitted optional key is legal; the rule falls back to its own
    default. Required means the key is *present*, not that it is
    truthy -- `links: {validate: false}` deliberately disables a
    check and is not the silent-typo failure mode.

    The accessors above cannot make these distinctions themselves:
    they return None both for a missing key and for one holding the
    wrong type, so the three states have to be separated before the
    accessors are reached.

    Arguments:
        config: the rule's configuration block, as parsed from YAML.
        allowed: every key the rule accepts, mapped to its type name
            from _CONFIG_TYPE_CHECKS.
        required: the keys whose absence would leave the rule inert.
        rule_id: the rule's id, named in every error message.

    Faults are reported in a fixed order -- unknown keys, then
    omitted required keys, then wrong-typed values -- so the message
    for a given configuration is deterministic. Unknown keys come
    first because a typo is both the likeliest fault and the one that
    makes the others misleading: a misspelled required key looks
    like an omission until its real name is pointed out.

    This is key-level validation only. Value-level checks that a rule
    already performs -- element names in `exclude` or `disallow`,
    entries in `valid_status_codes` -- run afterwards on values this
    function has confirmed are of the right shape.
    """
    for key in config:
        if key in allowed:
            continue
        if allowed:
            accepted = ", ".join(sorted(allowed))
            detail = f"Accepted keys: {accepted}."
        else:
            detail = "This rule accepts no configuration keys."
        raise ValueError(
            f"Rule {rule_id!r}: unknown configuration key "
            f"{key!r}. {detail}"
        )

    for key in required:
        if key not in config:
            raise ValueError(
                f"Rule {rule_id!r}: required configuration key "
                f"{key!r} is missing."
            )

    for key, value in config.items():
        type_name = allowed[key]
        if _CONFIG_TYPE_CHECKS[type_name](value):
            continue
        label = _CONFIG_TYPE_LABELS[type_name]
        raise ValueError(
            f"Rule {rule_id!r}: configuration key {key!r} expects "
            f"{label}, got {type(value).__name__!r}: {value!r}."
        )


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
            is_valid = _matches_status(
                response.status_code, valid_status_codes
            )
        else:
            is_valid = 200 <= response.status_code < 400
        return is_valid, response.status_code, None

    except requests.exceptions.Timeout:
        return False, None, "timeout"

    # Covers DNS errors, connection failures,
    # SSL issues, invalid URLs, etc.
    except requests.exceptions.RequestException as exc:
        return False, None, str(exc)
