# Standard library
from __future__ import annotations
import fnmatch
from typing import Any
from urllib.parse import urlparse

# Local
from tiredize.core_types import RuleResult
from tiredize.linter.utils import check_url_valid
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import get_config_dict
from tiredize.linter.utils import get_config_int
from tiredize.linter.utils import get_config_list
from tiredize.linter.utils import validate_config
from tiredize.markdown.types.document import Document


# Configuration keys this rule accepts, and the subset it requires.
# `validate` is required because the rule checks no links without it:
# enabling `links` with no `validate` would be a no-op. Present and
# false is legal and deliberately disables URL checking.
_RULE_ID = "links"
_ALLOWED_KEYS = {
    "exclude": "list",
    "headers": "dict",
    "timeout": "int",
    "valid_status_codes": "list",
    "validate": "bool",
}
_REQUIRED_KEYS = ("validate",)


def _is_excluded(url: str, exclusions: list[str]) -> bool:
    if not exclusions:
        return False
    hostname = urlparse(url).hostname or ""
    if not hostname:
        return False
    return any(
        fnmatch.fnmatchcase(hostname, pattern.lower())
        for pattern in exclusions
    )


def validate(
    document: Document,
    config: dict[str, Any],
) -> list[RuleResult]:
    """
    Validate document meets link requirements.

    Configuration:
        validate: bool - Enable link validation. Required; set it to
            false to leave the rule enabled but check nothing.
        exclude: list[str] - Hostname glob patterns to skip
            (e.g. '*.example.com'). Optional.
        headers: dict[str, str] - HTTP headers to include in requests.
            Optional.
        timeout: int - Timeout in seconds for link validation requests.
            Optional.
        valid_status_codes: list[int] - HTTP status codes treated as valid.
            Optional; defaults to all 2xx and 3xx codes.

    Raises:
        ValueError: the configuration names a key this rule does not
            accept, gives an accepted key a wrong-typed value, omits
            a required key, or holds a malformed exclude pattern or
            status code.
    """
    validate_config(config, _ALLOWED_KEYS, _REQUIRED_KEYS, _RULE_ID)

    cfg_validate = get_config_bool(config, "validate")
    if not cfg_validate:
        return []

    cfg_timeout = get_config_int(config, "timeout")
    cfg_headers = get_config_dict(config, "headers")
    cfg_exclusions = get_config_list(config, "exclude") or []
    for pattern in cfg_exclusions:
        if not isinstance(pattern, str):
            raise ValueError(
                "exclude entries must be strings, got "
                f"{type(pattern).__name__!r}: {pattern!r}"
            )

    cfg_valid_status = get_config_list(config, "valid_status_codes")
    valid_status_codes: list[int | str] | None = None
    if cfg_valid_status is not None:
        for code in cfg_valid_status:
            if isinstance(code, bool):
                raise ValueError(
                    "valid_status_codes entries must be integers or class "
                    f"wildcards like '2xx', got bool: {code!r}"
                )
            if isinstance(code, int):
                continue
            if (isinstance(code, str) and len(code) == 3
                    and code[0].isdigit() and code[1:].lower() == "xx"):
                continue
            raise ValueError(
                "valid_status_codes entries must be integers or class "
                f"wildcards like '2xx', got {type(code).__name__!r}: {code!r}"
            )
        valid_status_codes = list(cfg_valid_status)

    results: list[RuleResult] = []
    for section in document.sections:
        for link in section.links_inline:
            if _is_excluded(link.url, cfg_exclusions):
                continue
            is_valid, status_code, error_message = check_url_valid(
                document=document,
                url=link.url,
                timeout=cfg_timeout,
                headers=cfg_headers,
                valid_status_codes=valid_status_codes,
            )
            if not is_valid:
                position = link.position
                result = RuleResult(
                    message=(
                        f"Inline link '{link.url}' is not reachable. "
                        f"Status code: {status_code}, Error: {error_message}"
                    ),
                    position=position,
                    rule_id=None
                )
                results.append(result)

        for link in section.links_bracket:
            if _is_excluded(link.url, cfg_exclusions):
                continue
            is_valid, status_code, error_message = check_url_valid(
                document=document,
                url=link.url,
                timeout=cfg_timeout,
                headers=cfg_headers,
                valid_status_codes=valid_status_codes,
            )
            if not is_valid:
                position = link.position
                result = RuleResult(
                    message=(
                        f"Bracket link '{link.url}' is not reachable. "
                        f"Status code: {status_code}, Error: {error_message}"
                    ),
                    position=position,
                    rule_id=None
                )
                results.append(result)

        for link in section.links_bare:
            if _is_excluded(link.url, cfg_exclusions):
                continue
            is_valid, status_code, error_message = check_url_valid(
                document=document,
                url=link.url,
                timeout=cfg_timeout,
                headers=cfg_headers,
                valid_status_codes=valid_status_codes,
            )
            if not is_valid:
                position = link.position
                result = RuleResult(
                    message=(
                        f"Bare link '{link.url}' is not reachable. "
                        f"Status code: {status_code}, Error: {error_message}"
                    ),
                    position=position,
                    rule_id=None
                )
                results.append(result)

        for link in section.reference_definitions:
            if _is_excluded(link.url, cfg_exclusions):
                continue
            is_valid, status_code, error_message = check_url_valid(
                document=document,
                url=link.url,
                timeout=cfg_timeout,
                headers=cfg_headers,
                valid_status_codes=valid_status_codes,
            )
            if not is_valid:
                position = link.position
                result = RuleResult(
                    message=(
                        f"Reference link '{link.url}' is not reachable. "
                        f"Status code: {status_code}, Error: {error_message}"
                    ),
                    position=position,
                    rule_id=None
                )
                results.append(result)

    return results
