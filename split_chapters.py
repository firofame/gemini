import re, os

os.makedirs("Urdu_Chapters", exist_ok=True)

with open("Malfoozat-Maulana-Ilyas_OCR_Clean.txt", "r", encoding="utf-8") as f:
    text = f.read()

sections = re.split(r'^(?=### )', text, flags=re.MULTILINE)
sections = [s.strip() for s in sections if s.strip()]

names = []
for sec in sections:
    first_line = sec.split('\n')[0].strip()
    name = first_line.replace('### ', '').replace(' ', '_')
    name = re.sub(r'[^\w_]', '', name)
    names.append(name)

# Map to output filenames
file_map = [
    ("00_Dibacha", sections[0]),
    ("01_Qist_1", sections[1]),
    ("02_Qist_2", sections[2]),
    ("03_Qist_3", sections[3]),
    ("04_Qist_4", sections[4]),
    ("05_Qist_5", sections[5]),
    ("06_Qist_6", sections[6]),
    ("07_Qist_7", sections[7]),
    ("08_Qist_8", sections[8]),
    ("09_Qist_9", sections[9]),
    ("10_Qist_10", sections[10]),
    ("11_Qist_11", sections[11]),
]

for fname, content in file_map:
    path = f"Urdu_Chapters/{fname}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    print(f"  Created {path} ({len(content.splitlines())} lines)")

print(f"\nDone. {len(file_map)} files written to Urdu_Chapters/")
