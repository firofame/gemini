import os, subprocess
from pathlib import Path

for f in sorted(Path("Malayalam_Chapters").glob("*.md")):
    subprocess.run(["uv", "run", "tts.py", str(f)])
