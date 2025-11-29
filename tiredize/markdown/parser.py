from pathlib import Path
from tiredize.markdown.models.section import Section
import re
import typing
import yaml


RE_CODE_FENCE = re.compile(r"^``[`]+.*$")
RE_CODE_INLINE = re.compile(r"`[^`]*`")
RE_FRONT_MATTER_YAML = r"^---$"
RE_HEADER = re.compile(
    r"^(?P<hashes>#{1,6})\s(?P<title>.+?)$",
    re.MULTILINE
)
RE_LINK_INLINE = re.compile(
    r"(?P<image>!?)"
    r"\["
    r"(?P<title>.*?)"
    r"\]\("
    r"(?P<url>\s*\S+)"
    r"\s*?"
    r"\)"
)
RE_LINK_URL = re.compile(r"https?://\S+")
RE_LINK_REFERENCE = re.compile(
    r"\["
    r"(?P<title>[^^].*]?)"
    r"\]: "
    r"(?P<url>\s*\S*[\.\/]+\S*)"
    r"[\s]*?"
    r"(?P<desc>([\"\(\'].*[\"\'\)])*)",
    re.MULTILINE
)
RE_TABLE_DIV = re.compile(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$")
RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")


class Parser:
    fenced_lines: set[int] = None
    frontmatter_yaml: typing.Dict[str, str] = None
    markdown_text: str = None
    markdown_lines: typing.List[str] = None
    sections: typing.List["Section"] = None
    text: str

    def __init__(self, text):
        self.text = text

    def parse(self):
        self._extract_frontmatter()
        self._get_fenced_lines()
        self._extract_sections()

    def from_path(path: Path):
        text = path.read_text(encoding="utf-8")
        return Parser.from_text(text=text, path=path)

    def from_text(text: str, path: typing.Optional[Path] = None):
        parser = Parser(text)
        parser.parse()
        return Parser(text).parse()

    def _extract_frontmatter(self):
        """
        If there is frontmatter, we split the document into two parts
        representing the frontmatter and the actual markdown content.

        Returns (frontmatter_dict, markdown_text)

        If no front matter is present:
            frontmatter_dict is {}
            markdown_text is original text
        """

        split = re.split(
            RE_FRONT_MATTER_YAML,
            self.text,
            maxsplit=2,
            flags=re.MULTILINE
        )

        # We expect three parts: empty, yaml, markdown
        if len(split) < 3:
            self.frontmatter_yaml = {}
            self.markdown_text = self.text

        # If the first part isn't empty, we have unexpected text beforehand.
        # We treat this as content, not front matter.
        if len(split[0]) > 0:
            self.frontmatter_yaml = {}
            self.markdown_text = self.text

        # If we got this far, then we have something that looks like front
        # matter. We will try to parse it as YAML.
        frontmatter_dict = None
        try:
            frontmatter_dict = yaml.safe_load(split[1])
        except yaml.YAMLError:
            raise ValueError(f"Invalid YAML in frontmatter: {split[1]!r}")

        self.frontmatter_yaml = frontmatter_dict
        self.markdown_text = split[2].lstrip("\n")
        self.markdown_lines = self.markdown_text.splitlines()

    def _get_fenced_lines(self):
        """
        Identify all line numbers that are inside fenced code blocks.

        Includes the fence lines themselves.
        """
        self.fenced_lines = set()

        in_code: bool = False
        delimiter: str = "```"

        # Scan through all lines to find any that match the code fence regex
        for i, line in enumerate(self.markdown_text.splitlines(), start=1):

            # if we are already in a code block, mark this line
            if in_code:
                self.fenced_lines.add(i)

                # if this line is the matching delimiter, we exit code block
                if line.startswith(delimiter):
                    in_code = not in_code
                continue

            # if this is the start of a codeblock, store the closing delimiter
            if RE_CODE_FENCE.match(line):
                in_code = not in_code
                self.fenced_lines.add(i)
                delimiter = "`" * line.count("`")
                continue

    def _extract_sections(self):
        """
        Identify all sections in the document, skipping those inside fenced
        code.
        """

        self.sections = []

        new_section = None
        for line_num, line in enumerate(self.markdown_lines, start=1):

            # Ignore headings that appear inside fenced code
            if line_num in self.fenced_lines:
                continue

            # Check if this line is a heading
            m = RE_HEADER.match(line)
            if not m:
                continue

            new_section = Section(
                    header_level=len(m.group("hashes")),
                    header_title=m.group("title").strip(),
                    content="",
                    line_start=line_num,
                    line_end=-1,
                    subsections=[]
                )

            if len(self.sections) > 0:
                section_start = self.sections[-1].line_start
                section_end = line_num - 1
                self.sections[-1].line_end = section_end
                self.sections[-1].content = "\n".join(
                    self.markdown_lines[
                        section_start-1:section_end
                    ]
                ).strip()

            self.sections.append(new_section)

        section_start = self.sections[-1].line_start
        section_end = len(self.markdown_lines)
        new_section.line_end = section_end
        new_section.content = "\n".join(
            self.markdown_lines[
                section_start-1:section_end
            ]
        ).strip()

        for section_num, section in enumerate(self.sections):
            for i in range(section_num + 1, len(self.sections)):
                curr = self.sections[i]
                if curr.header_level > section.header_level:
                    section.subsections.append(curr)
                else:
                    break

        print(f"Extracted {len(self.sections)} sections")
