import typing


class Link:
    is_inline: bool
    is_reference: bool
    line: int
    url: str
    title: typing.Optional[str] = None
