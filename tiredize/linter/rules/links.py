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
from tiredize.markdown.types.document import Document


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
        validate: bool - Enable link validation
        exclude: list[str] - Hostname glob patterns to skip
            (e.g. '*.example.com')
        headers: dict[str, str] - HTTP headers to include in requests
        timeout: int - Timeout in seconds for link validation requests
    """
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

    results: list[RuleResult] = []
    for section in document.sections:
        for link in section.links_inline:
            if _is_excluded(link.url, cfg_exclusions):
                continue
            is_valid, status_code, error_message = check_url_valid(
                document=document,
                url=link.url,
                timeout=cfg_timeout,
                headers=cfg_headers
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
                headers=cfg_headers
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
                headers=cfg_headers
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
                headers=cfg_headers
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
