import re
from pathlib import Path

chapters_dir = Path("Malayalam_Chapters")
pattern = re.compile(r"## Part \d+\s*")

for md_file in sorted(chapters_dir.glob("*.md")):
    content = md_file.read_text(encoding="utf-8")
    new_content = pattern.sub("", content)
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    md_file.write_text(new_content.strip() + "\n", encoding="utf-8")
    print(f"Processed: {md_file.name}")
