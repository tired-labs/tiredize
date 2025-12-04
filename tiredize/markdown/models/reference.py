import typing
from dataclasses import dataclass


@dataclass(frozen=False)
class ReferenceDefinition:
    end: int
    start: int
    title: str
    url: str
    usage_images: typing.List["ImageReference"]
    usage_links: typing.List["LinkReference"]


@dataclass(frozen=False)
class LinkReference:
    definition: ReferenceDefinition
    end: int
    start: int
    text: str


@dataclass(frozen=False)
class ImageReference:
    definition: ReferenceDefinition
    end: int
    start: int
    text: typing.Optional[str]
