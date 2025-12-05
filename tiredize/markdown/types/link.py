from dataclasses import dataclass


@dataclass
class BareLink:
    end: int
    match: str
    start: int
    url: str


@dataclass
class BracketLink:
    end: int
    match: str
    start: int
    url: str


@dataclass
class InlineLink:
    end: int
    match: str
    start: int
    title: str
    url: str


RE_LINK_BRACKET = r"""
    <                            # Opening angle bracket
    (?P<url>https?:\/\/\S+)      # Capture the URL
    >                            # Closing angle bracket
"""

RE_LINK_INLINE = r"""
    (?P<image>!?)      # Look for leading ! to help filter out images
    \[                 # Opening bracket
    (?P<title>[^]]*)   # Capture the title
    \]\(               # Closing bracket, opening paren
    (?P<url>\s*\S+)    # Capture the URL
    \)                 # Closing paren
"""

RE_URL = r"""
    (?P<url>(https+:\/\/|(./|\\))\S+)  # Capture the URL
"""
