from pathlib import Path
from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.markdown.types.section import Section
import typing


class Document:
    path: typing.Optional[Path]
    frontmatter: typing.Optional[FrontMatter]
    sections: typing.List[Section]
    string: str
    string_markdown: str

    def __init__(self):
        self.path = None
        self.frontmatter = None
        self.sections: typing.List[Section] = []
        self.string = ""
        self.string_markdown = ""

    def load(self, path: Path = Path(), text: str = ""):
        if path != Path() and len(text):
            raise ValueError("Provide either 'path' or 'text', not both.")
        if path == Path() and len(text) == 0:
            raise ValueError("Provide either 'path' or 'text'.")
        if path.is_file():
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
        self.sections = Section.extract(md)
