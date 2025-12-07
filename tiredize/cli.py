from pathlib import Path
from tiredize.markdown.types.document import Document

tiredize_folder = Path(r"C:\Users\aprzybys\Code\TIRED\tooling\tiredize")
test_file = Path(r"tests\test-cases\good-frontmatter-and-markdown.md")
path = tiredize_folder / test_file

d = Document()
d.load(path=path)
print(d)
