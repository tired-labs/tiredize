# from pathlib import Path
# from tiredize.markdown.types.code import CodeBlock
# from tiredize.markdown.types.code import CodeInline
# from tiredize.markdown.types.document import Document
# from tiredize.markdown.types.header import Header
# from tiredize.markdown.types.image import InlineImage
# from tiredize.markdown.types.link import BareLink
# from tiredize.markdown.types.link import BracketLink
# from tiredize.markdown.types.link import InlineLink
# from tiredize.markdown.types.frontmatter import FrontMatter
# from tiredize.markdown.types.list import List
# from tiredize.markdown.types.quoteblock import QuoteBlock
# from tiredize.markdown.types.reference import ImageReference
# from tiredize.markdown.types.reference import LinkReference
# from tiredize.markdown.types.reference import ReferenceDefinition
# from tiredize.markdown.types.section import Section
# from tiredize.markdown.types.table import Table
# import typing


# class Parser:


#     def parse(self) -> Document:
#         result = Document(
#             frontmatter=None,
#             sections=[],
#             markdown_text="",
#             codeblock_lines=set(),
#             blockquote_lines=set()
#         )

#         result.frontmatter = FrontMatter.extract(self.text)
#         self._extract_frontmatter()
#         codeblocks = CodeBlock.extract(self.markdown_text)
#         # for codeblock in codeblocks:
#         #     # TODO
#         #     pass

#         quoteblocks = QuoteBlock.extract(self.markdown_text)
#         for quoteblock in quoteblocks:
#             start = quoteblock.position.line
#             lines_added = quoteblock.quote.count("\n")
#             end = start + lines_added
#             new_quoteblock_lines = set(range(start, end + 1))
#             result.blockquote_lines.update(new_quoteblock_lines)

#         # self._extract_blockquote_lines()
#         self._extract_sections()

#         for section in self.sections:
#             section.images_inline = InlineImage.extract(section.content)
#             section.quoteblocks = QuoteBlock.extract(section.content)

#             self._extract_images(section)
#             self._extract_reference_definitions(section)
#             self._extract_reference_usages(section)
#             self._extract_inline_code(section)
#             self._extract_links(section)
#         self._map_reference_usages()
#         return result

# def _extract_reference_usages(self, section: Section):
#     """
#     Extract reference usages from a section's content.
#     Ignoring anything in a code fence.
#     """

#     ref_usages = _search_all_re(
#         RE_REFERENCE_USAGE,
#         section.content.replace("\n", " ")
#     )

#     for ref_usage in ref_usages:
#         if ref_usage["groupdict"]["image"] == "!":
#             section.images_reference.append(
#                 ImageReference(
#                     definition=ref_usage["groupdict"]["reference"],
#                     end=ref_usage["end"],
#                     start=ref_usage["start"],
#                     text=ref_usage["groupdict"]["text"]
#                 )
#             )
#         else:
#             section.links_reference.append(
#                 LinkReference(
#                     definition=ref_usage["groupdict"]["reference"],
#                     end=ref_usage["end"],
#                     start=ref_usage["start"],
#                     text=ref_usage["groupdict"]["text"]
#                 )
#             )

# def _extract_reference_definitions(self, section: Section):
#     """
#     Extract reference definitions from a section's content.
#     Ignoring anything in a code fence.
#     """
#     # Reference definitions
#     reference_definitions = _search_all_re(
#         RE_REFERENCE_DEFINITION,
#         section.content
#     )
#     for link in reference_definitions:
#         new_ref_def = ReferenceDefinition(
#             end=link["end"],
#             start=link["start"],
#             title=link["groupdict"]["title"],
#             url=link["groupdict"]["url"],
#             usage_images=[],
#             usage_links=[]
#         )
#         section.reference_definitions.append(new_ref_def)
#         self.reference_definitions[new_ref_def.title] = new_ref_def

# def _extract_sections(self):
#     """
#     Identify all sections in the document, skipping those inside fenced
#     code.
#     """

#     self.sections = []
#     # new_section = Section(
#     #     code_inline=[],
#     #     content_raw="",
#     #     content="",
#     #     header_level=0,
#     #     header_title="",
#     #     images_inline=[],
#     #     images_reference=[],
#     #     line_end=0,
#     #     line_start=0,
#     #     links_bare=[],
#     #     links_bracket=[],
#     #     links_inline=[],
#     #     links_reference=[],
#     #     lists=[],
#     #     reference_definitions=[],
#     #     subsections=[],
#     #     tables=[]
#     # )

#     for line_num, line in enumerate(self.markdown_lines, start=1):

#         # Ignore headings that appear inside fenced code
#         if line_num in self.fenced_lines:
#             continue

#         # Check if this line is a heading, indicating a new section
#         heading_match = _search_all_re(RE_HEADER, line)
#         if (not heading_match) and (not len(heading_match) > 1):
#             continue

#         heading = heading_match[0]

#         new_section = Section(
#             code_block=[],
#             code_inline=[],
#             content_raw="",
#             content="",
#             header=Header(
#                 level=len(heading["groupdict"]["hashes"]),
#                 title=heading["groupdict"]["title"],
#                 start=heading["start"],
#                 end=heading["end"]
#             ),
#             images_inline=[],
#             images_reference=[],
#             line_end=-1,
#             line_start=line_num,
#             links_bare=[],
#             links_bracket=[],
#             links_inline=[],
#             links_reference=[],
#             lists=[],
#             quoteblocks=[],
#             reference_definitions=[],
#             subsections=[],
#             tables=[]
#         )

#         if len(self.sections) > 0:
#             section_start = self.sections[-1].line_start
#             section_end = line_num - 1
#             self.sections[-1].line_end = section_end
#             self.sections[-1].content_raw = "\n".join(
#                 self.markdown_lines[
#                     section_start-1:section_end
#                 ]
#             ).strip()

#         self.sections.append(new_section)

#     section_start = self.sections[-1].line_start
#     section_end = len(self.markdown_lines)
#     new_section.line_end = section_end
#     new_section.content_raw = "\n".join(
#         self.markdown_lines[
#             section_start-1:section_end
#         ]
#     ).strip()

#     # Housekeeping on all the sections we found
#     for section_num, section in enumerate(self.sections):

#       # Extract "sanitized" content blockquotes or fenced in code blocks
#         content_lines: list[str] = []
#         for line_num in range(section.line_start, section.line_end + 1):
#             if line_num in self.fenced_lines:
#                 continue
#             if line_num in self.blockquote_lines:
#                 continue
#             content_lines.append(self.markdown_lines[line_num - 1])
#         section.content = "\n".join(content_lines).strip()

#         # Add the subsections to each section that has them
#         for i in range(section_num + 1, len(self.sections)):
#             curr = self.sections[i]
#             if curr.header.level > section.header.level:
#                 section.subsections.append(curr)
#             else:
#                 break

# def _map_reference_usages(self):
#     """
#     For every ReferenceDefinition, find all usages in links and images
#     and map them back to the definition.
#     """
#     for section in self.sections:
#         for link_ref in section.links_reference:
#             ref_def = self.reference_definitions.get(link_ref.definition)
#             link_ref.definition = ref_def
#             if ref_def:
#                 ref_def.usage_links.append(link_ref)
#         for img_ref in section.images_reference:
#             ref_def = self.reference_definitions.get(img_ref.definition)
#             img_ref.definition = ref_def
#             if ref_def:
#                 ref_def.usage_images.append(img_ref)
