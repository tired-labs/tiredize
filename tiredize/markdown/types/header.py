from dataclasses import dataclass
from tiredize.core_types import Position
from tiredize.markdown.types.code import CodeBlock
from tiredize.markdown.utils import sanitize_text
from tiredize.markdown.utils import search_all_re
import re
import typing


@dataclass(frozen=False)
class Header:
    level: int
    position: Position
    slug: str
    string: str
    title: str

    RE_HEADER = r"""
        (?<![^|\n])           # Start of line, but don't capture it
        (?P<hashes>\#{1,6})   # One to six hash characters
        \s+                   # Whitespace
        (?P<title>[^\n]+)     # Capture anything after that as the title
    """

    @staticmethod
    def extract(text: str, base_offset: int = 0) -> typing.List["Header"]:
        """
        Extract markdown titles from a section.
        As we are expecting a section's text to be the input, this must be the
        first thing appearing in the text provided.
        """
        matches = search_all_re(
            Header.RE_HEADER,
            CodeBlock.sanitize(text)
        )

        result: list[Header] = []
        header_titles: list[str] = []
        for match in matches:
            level = len(match.group("hashes"))
            title = match.group("title")
            header_titles.append(title)
            position = Position(
                offset=base_offset + match.start(),
                length=match.end() - match.start()
            )

            result.append(
                Header(
                    level=level,
                    position=position,
                    slug=Header.slugify_header(
                        title,
                        existing=header_titles[:-1]
                    ),
                    string=match.group(),
                    title=title
                )
            )
        return result

    @staticmethod
    def sanitize(text: str) -> str:
        """
        Replace any Headers with whitespace
        """
        return sanitize_text(Header.RE_HEADER, text)

    @staticmethod
    def slugify_header(
        title: str,
        existing: typing.Optional[list[str]] = None
    ) -> str:
        """
        Generate GitHub-Flavored Markdown (GFM) anchor slugs for all headings.

        Steps followed:
        1. Lowercase the text.
        2. Remove punctuation characters except hyphens and spaces.
        3. Convert spaces to hyphens.
        4. Collapse multiple hyphens.
        5. Strip leading/trailing hyphens.
        6. If the slug already exists, append "-1", "-2", etc.

        Parameters:
        title: The raw heading text, e.g. "Section One: Good Stuff".
        existing: Optional list tracking previously-seen titles.

        Returns:
        A list of unique slugs corresponding to the input headings.
        """
        if title == "":
            title = "section"

        slug = title.lower()
        slug = re.sub(r"[^a-z0-9 \-]", "", slug)
        slug = slug.replace(" ", "-")
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        slug = f"#{slug}"

        seen: typing.Dict[str, int] = {}
        for e in (existing or []):
            if e not in seen:
                seen[e] = 1
            else:
                seen[e] += 1

        if title in seen:
            if seen[title] > 0:
                slug = f"{slug}-{seen[title]}"

        return slug
