from pathlib import Path
from tiredize.markdown.models.image import InlineImage
from tiredize.markdown.models.link import BareLink
from tiredize.markdown.models.link import BracketLink
from tiredize.markdown.models.link import InlineLink
from tiredize.markdown.models.section import Section
from tiredize.markdown.models.reference import ReferenceDefinition
from tiredize.markdown.models.reference import ImageReference
from tiredize.markdown.models.reference import LinkReference
# from tiredize.markdown.models.list import List
# from tiredize.markdown.models.table import Table
import re
import typing
import yaml


_RE_BLOCKQUOTE = r"""
    ^                  # Must be at the start of a line
    >                  # Blockquote character
    (?P<quote>.*)      # Capture anything after that
    $                  # Line ends here
"""

_RE_CODE_FENCE = r"""
    ^                     # Must be at the start of a line
    (?P<delimiter>``[`]+) # Opening backticks (three or more)
    (?P<syntax>.*)        # Capture the syntax if present
    $                     # Line ends here
"""

_RE_CODE_INLINE = r"""
    [^\S\s^]?    # Exclude any characters before the backtick
    `            # Opening backtick
    [^\n`]+      # Capture anything except backtick or newline
    `            # Closing backtick
"""

_RE_FRONT_MATTER_YAML = r"^---$"

_RE_HEADER = r"""
    ^                     # Heading must start at beginning of line
    (?P<hashes>\#{1,6})   # One to six hash characters
    \s                    # Capture one space, the rest will be in title
    (?P<title>.+?)        # Capture heading title
    $                     # Heading ends when the line ends
"""

_RE_IMAGE_INLINE = r"""
    !\[                              # Opening (exclamation mark and bracket)
    (?P<alttext>[^]]*)               # Capture the alt-text
    \]\(                             # Closing bracket, opening paren
    (?P<url>[\s]*[^\s\)]*)           # Capture the URL
    \s*"*                            # Support for optional title
    (?P<title>.*?)                   # Capture optional title text
    "*?\s*?\)                        # Closing characters
"""

_RE_LINK_BRACKET = r"""
    <                            # Opening angle bracket
    (?P<url>https?:\/\/\S+)      # Capture the URL
    >                            # Closing angle bracket
"""

_RE_LINK_INLINE = r"""
    (?P<image>!?)      # Look for leading ! to help filter out images
    \[                 # Opening bracket
    (?P<title>[^]]*)   # Capture the title
    \]\(               # Closing bracket, opening paren
    (?P<url>\s*\S+)    # Capture the URL
    \)                 # Closing paren
"""

_RE_REFERENCE_DEFINITION = r"""
    ^\[                        # References are defined at start of a line
    (?P<title>[^^].*]?)        # Capture the title
    \]:\s+                     # Closing bracket, colon, leading spaces
    (?P<url>\S*[#\.\/]+\S*)    # Capture the URL
    [\s]*?                     # Optional whitespace
    (?P<desc>([\"\(\'].*[\"\'\)])*)  # Capture optional description in quotes
"""

_RE_REFERENCE_USAGE = r"""
    (?P<image>!?)               # Look for leading ! to identify images
    (\[(?P<text>[^\]]+)\]\s*)?  # Capture the link text if present
    \[                          # Opening bracket
    (?P<reference>[^\]]+)       # Capture the reference title
    \]                          # Closing bracket
    [^(:]                       # Ensure not followed by ( or :
"""

# RE_TABLE_DIV = re.compile(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$")
# RE_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")

_RE_URL = r"""
    (?P<url>https+:\/\/\S+)  # Capture the URL
"""


class Parser:
    blockquote_lines: set[int] = set()
    fenced_lines: set[int] = set()
    frontmatter_yaml: typing.Dict[str, str] = {}
    reference_definitions: typing.Dict[str, ReferenceDefinition] = {}
    markdown_text: str = ""
    markdown_lines: typing.List[str] = []
    sections: typing.List["Section"] = []
    text: str

    def __init__(self, text: str):
        self.text = text

    @classmethod
    def from_path(cls, path: Path) -> "Parser":
        text = path.read_text(encoding="utf-8")
        return cls.from_text(text)

    @classmethod
    def from_text(cls, text: str) -> "Parser":
        parser = cls(text)
        parser.parse()
        return parser

    def parse(self):
        self._extract_frontmatter()
        self._extract_fenced_lines()
        self._extract_blockquote_lines()
        self._extract_sections()
        for section in self.sections:
            self._extract_images(section)
            self._extract_reference_definitions(section)
            self._extract_reference_usages(section)
            self._extract_inline_code(section)
            self._extract_links(section)
        self._map_reference_usages()

    def _extract_blockquote_lines(self):
        """
        Identify all line numbers that are blockquoted.

        Ignore if the blockquoted lines are within a fenced code block.
        """
        self.blockquote_lines = set()

        # Scan through all lines to find any that match the blockquote regex
        for i, line in enumerate(self.markdown_text.splitlines(), start=1):

            # Add the line if it is in a blockquote
            if re.match(_RE_BLOCKQUOTE, line, re.MULTILINE | re.VERBOSE):
                self.blockquote_lines.add(i)
                continue

    def _extract_fenced_lines(self):
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
            if re.match(_RE_CODE_FENCE, line, re.VERBOSE):
                in_code = not in_code
                self.fenced_lines.add(i)
                delimiter = "`" * line.count("`")
                continue

    def _extract_frontmatter(self):
        """
        If there is frontmatter, we split the document into two parts
        representing the frontmatter and the actual markdown content.

        Returns (frontmatter_dict, markdown_text)

        If no front matter is present:
            frontmatter_dict is {}
            markdown_text is original text
        """

        if not self.text.startswith("---"):
            self.frontmatter_yaml = {}
            self.markdown_text = self.text
            self.markdown_lines = self.markdown_text.splitlines()
            return

        split = re.split(
            _RE_FRONT_MATTER_YAML,
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

    def _extract_images(self, section: Section):
        """
        Extract images from a section's content.
        Ignoring anything in a code fence.
        """
        images = _search_all_re(
            _RE_IMAGE_INLINE,
            section.content.replace("\n", " ")
        )

        for image in images:
            section.images_inline.append(
                InlineImage(
                    alt_text=image["groupdict"]["alttext"],
                    end=image["end"],
                    start=image["start"],
                    title_text=image["groupdict"]["title"],
                    url=image["groupdict"]["url"]
                )
            )

    def _extract_inline_code(self, section: Section):
        """
        Extract inline code from a section's content.
        Ignoring anything in a code fence.
        """
        codes = _search_all_re(
            _RE_CODE_INLINE,
            section.content.replace("\n", " ")
        )

        for code in codes:
            section.code_inline.append(
                code["match"]
            )

    def _extract_links(self, section: Section):
        """
        Extract links from a section's content.
        Ignoring anything in a code fence.
        """

        links_bare = _search_all_re(_RE_URL, section.content)

        # Inline links
        links_inline: list[dict[typing.Any, typing.Any]] = _search_all_re(
            _RE_LINK_INLINE,
            section.content.replace("\n", " ")
        )
        for inline in links_inline:
            section.links_inline.append(
                InlineLink(
                    end=inline["end"],
                    start=inline["start"],
                    title=inline["groupdict"]["title"],
                    url=inline["groupdict"]["url"]
                )
            )
            for bare in links_bare:
                if bare["start"] >= inline["start"]:
                    bare_end = bare["start"] + len(inline["groupdict"]["url"])
                    if bare_end <= inline["end"]:
                        links_bare.remove(bare)

        # Bracket links
        links_bracket: list[dict[typing.Any, typing.Any]] = _search_all_re(
            _RE_LINK_BRACKET,
            section.content.replace("\n", " ")
        )
        for bracket in links_bracket:
            section.links_bracket.append(
                BracketLink(
                    end=bracket["end"],
                    start=bracket["start"],
                    url=bracket["groupdict"]["url"]
                )
            )
            for bare in links_bare:
                if bare["start"] >= bracket["start"]:
                    bare_end = bare["start"] + len(bracket["groupdict"]["url"])
                    if bare_end <= bracket["end"]:
                        links_bare.remove(bare)

        # Remove any bare links that were already captured as images
        for image in section.images_inline:
            for bare in links_bare:
                if bare["start"] >= image.start:
                    if bare["end"] <= image.end:
                        links_bare.remove(bare)

        # Remove any bare links that were already captured as reference defs
        for reference_definition in section.reference_definitions:
            for bare in links_bare:
                if bare["start"] >= reference_definition.start:
                    if bare["end"] <= reference_definition.end:
                        links_bare.remove(bare)

        for bare in links_bare:
            section.links_bare.append(
                BareLink(
                    end=bare["end"],
                    start=bare["start"],
                    url=bare["groupdict"]["url"]
                )
            )

    def _extract_reference_usages(self, section: Section):
        """
        Extract reference usages from a section's content.
        Ignoring anything in a code fence.
        """

        ref_usages = _search_all_re(
            _RE_REFERENCE_USAGE,
            section.content.replace("\n", " ")
        )

        for ref_usage in ref_usages:
            if ref_usage["groupdict"]["image"] == "!":
                section.images_reference.append(
                    ImageReference(
                        definition=ref_usage["groupdict"]["reference"],
                        end=ref_usage["end"],
                        start=ref_usage["start"],
                        text=ref_usage["groupdict"]["text"]
                    )
                )
            else:
                section.links_reference.append(
                    LinkReference(
                        definition=ref_usage["groupdict"]["reference"],
                        end=ref_usage["end"],
                        start=ref_usage["start"],
                        text=ref_usage["groupdict"]["text"]
                    )
                )

    def _extract_reference_definitions(self, section: Section):
        """
        Extract reference definitions from a section's content.
        Ignoring anything in a code fence.
        """
        # Reference definitions
        reference_definitions = _search_all_re(
            _RE_REFERENCE_DEFINITION,
            section.content
        )
        for link in reference_definitions:
            new_ref_def = ReferenceDefinition(
                end=link["end"],
                start=link["start"],
                title=link["groupdict"]["title"],
                url=link["groupdict"]["url"],
                usage_images=[],
                usage_links=[]
            )
            section.reference_definitions.append(new_ref_def)
            self.reference_definitions[new_ref_def.title] = new_ref_def

    def _extract_sections(self):
        """
        Identify all sections in the document, skipping those inside fenced
        code.
        """

        self.sections = []
        new_section = Section(
            code_inline=[],
            content_raw="",
            content="",
            header_level=0,
            header_title="",
            images_inline=[],
            images_reference=[],
            line_end=0,
            line_start=0,
            links_bare=[],
            links_bracket=[],
            links_inline=[],
            links_reference=[],
            lists=[],
            reference_definitions=[],
            subsections=[],
            tables=[]
        )

        for line_num, line in enumerate(self.markdown_lines, start=1):

            # Ignore headings that appear inside fenced code
            if line_num in self.fenced_lines:
                continue

            # Check if this line is a heading
            m = re.match(_RE_HEADER, line, re.MULTILINE | re.VERBOSE)
            if not m:
                continue

            new_section = Section(
                code_inline=[],
                content_raw="",
                content="",
                header_level=len(m.group("hashes")),
                header_title=m.group("title"),
                images_inline=[],
                images_reference=[],
                line_end=-1,
                line_start=line_num,
                links_bare=[],
                links_bracket=[],
                links_inline=[],
                links_reference=[],
                lists=[],
                reference_definitions=[],
                subsections=[],
                tables=[]
            )

            if len(self.sections) > 0:
                section_start = self.sections[-1].line_start
                section_end = line_num - 1
                self.sections[-1].line_end = section_end
                self.sections[-1].content_raw = "\n".join(
                    self.markdown_lines[
                        section_start-1:section_end
                    ]
                ).strip()

            self.sections.append(new_section)

        section_start = self.sections[-1].line_start
        section_end = len(self.markdown_lines)
        new_section.line_end = section_end
        new_section.content_raw = "\n".join(
            self.markdown_lines[
                section_start-1:section_end
            ]
        ).strip()

        # Housekeeping on all the sections we found
        for section_num, section in enumerate(self.sections):

            # Extract "sanitized" content blockquotes or fenced in code blocks
            content_lines: list[str] = []
            for line_num in range(section.line_start, section.line_end + 1):
                if line_num in self.fenced_lines:
                    continue
                if line_num in self.blockquote_lines:
                    continue
                content_lines.append(self.markdown_lines[line_num - 1])
            section.content = "\n".join(content_lines).strip()

            # Add the subsections to each section that has them
            for i in range(section_num + 1, len(self.sections)):
                curr = self.sections[i]
                if curr.header_level > section.header_level:
                    section.subsections.append(curr)
                else:
                    break

    def _map_reference_usages(self):
        """
        For every ReferenceDefinition, find all usages in links and images
        and map them back to the definition.
        """
        for section in self.sections:
            for link_ref in section.links_reference:
                ref_def = self.reference_definitions.get(link_ref.definition)
                link_ref.definition = ref_def
                if ref_def:
                    ref_def.usage_links.append(link_ref)
            for img_ref in section.images_reference:
                ref_def = self.reference_definitions.get(img_ref.definition)
                img_ref.definition = ref_def
                if ref_def:
                    ref_def.usage_images.append(img_ref)


def _search_all_re(
        pattern: str, string: str) -> list[dict[typing.Any, typing.Any]]:

    result: list[dict[typing.Any, typing.Any]] = []
    for match in re.finditer(pattern, string, re.MULTILINE | re.VERBOSE):
        entry: dict[typing.Any, typing.Any] = {
            "match": match.group(),
            "groupdict": match.groupdict(),
            "start": match.start(),
            "end": match.end()
        }
        result.append(entry)

    return result
