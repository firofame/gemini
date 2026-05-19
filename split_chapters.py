import re
import os

input_file = "Fazail-e-Sadaqat_OCR_Clean.txt"
# Create a folder name from the input file name (e.g., "Fazail-e-Sadaqat")
folder_name = input_file.split("_")[0]
output_dir = os.path.join(folder_name, "Urdu_Chapters")

# Create the output directory
os.makedirs(output_dir, exist_ok=True)

# Read the file
with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

# In Fazail-e-Sadaqat, '### ' is also used for sub-headings (e.g., '### آیات', '### احادیث').
# We use a specific regex to split ONLY on the main Fasal (Chapter) markers.
chapter_pattern = r'^(?=### (?:فصل اول|دوسری فصل|تیسری فصل|چوتھی فصل|پانچویں فصل|چھٹی فصل|ساتویں فصل))'

sections = re.split(chapter_pattern, text, flags=re.MULTILINE)
sections = [s.strip() for s in sections if s.strip()]

# Verify we got the expected 8 sections (1 Intro/Dibacha + 7 Chapters)
if len(sections) != 8:
    print(f"Warning: Expected 8 sections, but found {len(sections)}.")

# Map to the new output filenames
file_map = [
    ("00_Muqaddimah", sections[0]), # Contains Title, Bismillah, and Intro
    ("01_Fasal_1", sections[1]),    # فصل اول
    ("02_Fasal_2", sections[2]),    # دوسری فصل
    ("03_Fasal_3", sections[3]),    # تیسری فصل
    ("04_Fasal_4", sections[4]),    # چوتھی فصل
    ("05_Fasal_5", sections[5]),    # پانچویں فصل
    ("06_Fasal_6", sections[6]),    # چھٹی فصل
    ("07_Fasal_7", sections[7]),    # ساتویں فصل
]

for fname, content in file_map:
    path = os.path.join(output_dir, f"{fname}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    print(f"  Created {path} ({len(content.splitlines())} lines)")

print(f"\nDone. {len(file_map)} files written to {output_dir}/")