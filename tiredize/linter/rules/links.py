from __future__ import annotations
from tiredize.core_types import RuleResult
from tiredize.linter.utils import check_url_valid
from tiredize.linter.utils import get_config_bool
from tiredize.linter.utils import get_config_dict
from tiredize.linter.utils import get_config_int
from tiredize.markdown.types.document import Document
import typing


def validate(
    document: Document,
    config: typing.Dict[str, typing.Any],
) -> typing.List[RuleResult]:
    """
    Validate document meets link requirements.

    Configuration:
        validate: bool - Enable link validation
        ignore_domains: list[str] - Domains to ignore during validation
        ignore_status_codes: list[int] - HTTP status codes to ignore
        timeout: int - Timeout for link validation requests
    """
    cfg_validate = get_config_bool(config, "validate")
    if not cfg_validate:
        return []

    cfg_timeout = get_config_int(config, "timeout")
    cfg_headers = get_config_dict(config, "headers")
    # cfg_ignore_codes = get_config_list(config, "ignore_status_codes")

    results: typing.List[RuleResult] = []
    for section in document.sections:
        for link in section.links_inline:
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
