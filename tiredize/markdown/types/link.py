from dataclasses import dataclass
import typing


@dataclass
class BareLink:
    end: int
    match: str
    start: int
    url: str

    RE_URL = r"""
        (?P<url>(https+:\/\/|(./|\\))\S+)  # Capture the URL
    """

    @staticmethod
    def extract(text: str) -> typing.List["BareLink"]:
        if len(text) == 0:
            return []
        result: typing.List[BareLink] = []
        return result


@dataclass
class BracketLink:
    end: int
    match: str
    start: int
    url: str

    RE_LINK_BRACKET = r"""
        <                            # Opening angle bracket
        (?P<url>https?:\/\/\S+)      # Capture the URL
        >                            # Closing angle bracket
    """

    @staticmethod
    def extract(text: str) -> typing.List["BracketLink"]:
        if len(text) == 0:
            return []
        result: typing.List[BracketLink] = []
        return result


@dataclass
class InlineLink:
    end: int
    match: str
    start: int
    title: str
    url: str

    RE_LINK_INLINE = r"""
        (?P<image>!?)      # Look for leading ! to help filter out images
        \[                 # Opening bracket
        (?P<title>[^]]*)   # Capture the title
        \]\(               # Closing bracket, opening paren
        (?P<url>\s*\S+)    # Capture the URL
        \)                 # Closing paren
    """

    @staticmethod
    def extract(text: str) -> typing.List["InlineLink"]:
        if len(text) == 0:
            return []
        result: typing.List[InlineLink] = []
        return result
