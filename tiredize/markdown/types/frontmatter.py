from dataclasses import dataclass
from tiredize.core_types import Position
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
import typing
import yaml


@dataclass(frozen=False)
class FrontMatter:
    content: typing.Dict[typing.Any, typing.Any]
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
    ) -> typing.Optional["FrontMatter"]:
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
