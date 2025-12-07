from pathlib import Path
from tiredize.markdown.types.frontmatter import FrontMatter
from tiredize.markdown.types.section import Section
import typing


class Document:
    path: typing.Optional[Path] = None
    frontmatter: typing.Optional[FrontMatter] = None
    sections: typing.List[Section] = []
    string: str = ""

    def load(self, path: Path = Path(), text: str = ""):
        if path != Path() and len(text):
            raise ValueError("Provide either 'path' or 'text', not both.")
        if path == Path() and len(text) == 0:
            raise ValueError("Provide either 'path' or 'text'.")
        if path.is_file():
            Document.path = path
            with open(Path(path), "r", encoding="utf-8") as f:
                text = f.read()
                self.string = text
        if len(text):
            self.string = text
        self._parse()

    def _parse(self):
        self.frontmatter = FrontMatter.extract(self.string)
        markdown = self.string[self.frontmatter.position.length + 1:]
        print("Done with parsing! " + markdown[0:256])
        # codeblocks = CodeBlock.extract(self.markdown_text)
        # # for codeblock in codeblocks:
        # #     # TODO
        # #     pass

        # quoteblocks = QuoteBlock.extract(self.markdown_text)
        # for quoteblock in quoteblocks:
        #     start = quoteblock.position.line
        #     lines_added = quoteblock.quote.count("\n")
        #     end = start + lines_added
        #     new_quoteblock_lines = set(range(start, end + 1))
        #     result.blockquote_lines.update(new_quoteblock_lines)

        # # self._extract_blockquote_lines()
        # self._extract_sections()

        # for section in self.sections:
        #     section.images_inline = InlineImage.extract(section.content)
        #     section.quoteblocks = QuoteBlock.extract(section.content)

        #     self._extract_images(section)
        #     self._extract_reference_definitions(section)
        #     self._extract_reference_usages(section)
        #     self._extract_inline_code(section)
        #     self._extract_links(section)
        # self._map_reference_usages()
