from pathlib import Path
from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.markdown.types.section import Section
import typing


class Document:
    _path: typing.Optional[Path] = None
    frontmatter: typing.Optional[FrontMatter] = None
    sections: typing.List[Section] = []
    _string: str = ""
    _string_markdown: str = ""

    def load(self, path: Path = Path(), text: str = ""):
        if path != Path() and len(text):
            raise ValueError("Provide either 'path' or 'text', not both.")
        if path == Path() and len(text) == 0:
            raise ValueError("Provide either 'path' or 'text'.")
        if path.is_file():
            self._path = path
            with open(Path(path), "r", encoding="utf-8") as f:
                self._string = f.read()
        if len(text):
            self._string = text
        self._parse()

    def _parse(self):
        # Separate out the frontmatter before we dive into markdown
        self.frontmatter = FrontMatter.extract(self._string)
        md = self._string
        if self.frontmatter is not None:
            md = self._string[self.frontmatter.position.length + 1:]
        self._string_markdown = md
        self.sections = Section.extract(md)
