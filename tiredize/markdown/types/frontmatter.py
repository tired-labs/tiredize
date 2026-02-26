# Standard library
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

# Third-party
import yaml

# Local
from tiredize.core_types import Position
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re


@dataclass(frozen=False)
class FrontMatter:
    content: dict[Any, Any]
    position: Position
    string: str

    RE_FRONT_MATTER_YAML = r"""
        ^                  # Must be at the start of a line
        [-]{3}             # Three dashes represents YAML frontmatter
        \n                 # Newline
        (?P<yaml>[\s\S]*?) # Capture anything as YAML content
        \n                 # Newline
        [-]{3}             # Three dashes represents end of YAML frontmatter
        \n                 # Newline
    """

    @staticmethod
    def extract(
        text: str,
        base_offset: int = 0
    ) -> FrontMatter | None:
        """
        Extract frontmatter from text.
        """
        matches = search_all_re(
            FrontMatter.RE_FRONT_MATTER_YAML,
            text
        )
        match = matches[0] if matches else None
        if not match:
            return None
        position = Position(
            offset=base_offset + match.start(),
            length=match.end() - match.start()
        )
        try:
            content = yaml.safe_load(match.group("yaml"))
        except yaml.YAMLError:
            return None

        result = FrontMatter(
            content=content,
            position=position,
            string=match.group(),
        )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any FrontMatter with whitespace
        """
        return sanitize_text(FrontMatter.RE_FRONT_MATTER_YAML, text)
