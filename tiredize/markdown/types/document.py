from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from dataclasses import replace
from pathlib import Path
from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.markdown.types.section import Section
import bisect
import typing


def _new_sections() -> list[Section]:
    return []


@dataclass
class Document:
    frontmatter: typing.Optional[FrontMatter] = None
    _line_starts: typing.List[int] = field(init=False, repr=False)
    path: typing.Optional[Path] = None
    sections: typing.List["Section"] = field(default_factory=_new_sections)
    string_markdown: str = ""
    string: str = ""

    def __post_init__(self) -> None:
        self._line_starts = [0]

    def _build_line_index(self) -> None:
        self._line_starts = [0]
        for i, ch in enumerate(self.string):
            if ch == "\n":
                self._line_starts.append(i + 1)

    def line_col(self, offset: int) -> tuple[int, int]:
        """
        Return (line_number, column) for a document-root offset.

        line_number is 1-based.
        column is 0-based.
        """
        if offset < 0:
            offset = 0
        doc_len = len(self.string)
        if offset > doc_len:
            offset = doc_len

        line_index = bisect.bisect_right(self._line_starts, offset) - 1
        line_start = self._line_starts[line_index]
        return line_index + 1, offset - line_start

    def load(self, path: Path = Path(), text: str = ""):
        if path != Path() and len(text):
            raise ValueError("Provide either 'path' or 'text', not both.")
        if path == Path() and len(text) == 0:
            raise ValueError("Provide either 'path' or 'text'.")
        if path != Path():
            if not path.is_file():
                raise FileNotFoundError(f"Path does not exist: {path}")
            self.path = path
            with open(Path(path), "r", encoding="utf-8") as f:
                self.string = f.read()
        if len(text):
            self.string = text
        self._parse()

    def _parse(self):
        # Separate out the frontmatter before we dive into markdown
        self.frontmatter = FrontMatter.extract(self.string)
        md = self.string
        if self.frontmatter is not None:
            md = self.string[self.frontmatter.position.length + 1:]
        self.string_markdown = md
        base_offset = 0
        if self.frontmatter:
            base_offset = self.frontmatter.position.length + 1
        self.sections = Section.extract(text=md, base_offset=base_offset)

        header_titles: list[str] = []
        for i, section in enumerate(self.sections):
            header = section.header
            header_titles.append(header.title)
            slug = header.slugify_header(
                header.title,
                existing=header_titles[:-1]
            )
            new_header = replace(section.header, slug=slug)
            self.sections[i] = replace(section, header=new_header)
        self._build_line_index()
