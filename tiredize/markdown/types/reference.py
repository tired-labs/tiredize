import typing
from dataclasses import dataclass


@dataclass(frozen=False)
class ReferenceDefinition:
    end: int
    match: str
    start: int
    title: str
    url: str
    usage_images: typing.List["ImageReference"]
    usage_links: typing.List["LinkReference"]


@dataclass(frozen=False)
class LinkReference:
    definition: ReferenceDefinition
    end: int
    match: str
    start: int
    text: str


@dataclass(frozen=False)
class ImageReference:
    definition: ReferenceDefinition
    end: int
    match: str
    start: int
    text: typing.Optional[str]


RE_REFERENCE_DEFINITION = r"""
    ^\[                        # References are defined at start of a line
    (?P<title>[^^].*]?)        # Capture the title
    \]:\s+                     # Closing bracket, colon, leading spaces
    (?P<url>\S*[#\.\/]+\S*)    # Capture the URL
    [\s]*?                     # Optional whitespace
    (?P<desc>([\"\(\'].*[\"\'\)])*)  # Capture optional description in quotes
"""

RE_REFERENCE_USAGE = r"""
    (?P<image>!?)               # Look for leading ! to identify images
    (\[(?P<text>[^\]]+)\]\s*)?  # Capture the link text if present
    \[                          # Opening bracket
    (?P<reference>[^\]]+)       # Capture the reference title
    \]                          # Closing bracket
    [^(:]                       # Ensure not followed by ( or :
"""
