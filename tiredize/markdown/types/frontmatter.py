from dataclasses import dataclass
from tiredize.markdown.utils import get_position_from_match
from tiredize.markdown.utils import search_all_re
from tiredize.types import Position
import typing
import yaml


@dataclass(frozen=True)
class FrontMatter:
    content: typing.Dict[typing.Any, typing.Any]
    position: Position
    string: str

    _RE_FRONT_MATTER_YAML = r"""
        ^                  # Must be at the start of a line
        [-]{3}             # Three dashes represents YAML frontmatter
        \n                 # Newline
        (?P<yaml>[\s\S]*?) # Capture anything as YAML content
        \n                 # Newline
        [-]{3}             # Three dashes represents end of YAML frontmatter
        \n                 # Newline
    """

    @staticmethod
    def extract(text: str) -> typing.Optional["FrontMatter"]:
        """
        Extract frontmatter from text.
        """
        matches = search_all_re(
            FrontMatter._RE_FRONT_MATTER_YAML,
            text
        )
        match = matches[0] if matches else None
        if not match:
            return None

        line_num, offset, length = get_position_from_match(match, text)
        try:
            content = yaml.safe_load(match.group("yaml"))
        except yaml.YAMLError:
            return None

        result = FrontMatter(
            content=content,
            position=Position(
                line=line_num,
                offset=offset,
                length=length
            ),
            string=match.group(),
        )
        return result
