from pathlib import Path
from tiredize.markdown.parser import Parser

p = Path("README.md")
x = Parser.from_path(p)
print(x)
