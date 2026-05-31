import re
import os

input_file = os.path.join("Hayat al-Sahaba", "Hayat us-Sahabah - Maulana Muhammad Yusuf Khandalwi - Volume 1_OCR_Clean.txt")
# Create the output directory inside the same folder as the input file
output_dir = os.path.join(os.path.dirname(input_file), "Arabic_Chapters")

# Create the output directory
os.makedirs(output_dir, exist_ok=True)

# Read the file
with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

# In Hayat us-Sahabah, the main chapters (Babs) are marked with diacritic/tashkeel headers:
# 1. ### الْبَابُ الْأَوَّلُ
# 2. ### الْبَابُ الثَّانِي
# 3. ### الْبَابُ الثَّالِثُ
# 4. # الْبَابُ الرَّابِعُ     (Note the single '#' prefix for chapter 4 in the OCR source)
# 5. ### الْبَابُ الْخَامِسُ
# 6. ### الْبَابُ السَّادِسُ
# We use a specific regex to split ONLY on these main chapter markers.
chapter_pattern = r'^(?=### الْبَابُ الْأَوَّلُ|### الْبَابُ الثَّانِي|### الْبَابُ الثَّالِثُ|# الْبَابُ الرَّابِعُ|### الْبَابُ الْخَامِسُ|### الْبَابُ السَّادِسُ)'

sections = re.split(chapter_pattern, text, flags=re.MULTILINE)
sections = [s.strip() for s in sections if s.strip()]

# Verify we got the expected 7 sections (1 Intro/Muqaddimah + 6 Chapters)
if len(sections) != 7:
    print(f"Warning: Expected 7 sections, but found {len(sections)}.")

# Map to the new output filenames
file_map = [
    ("00_Muqaddimah", sections[0]), # Contains Title, Bismillah, and Intro
    ("01_Bab_1", sections[1]),      # الباب الأول
    ("02_Bab_2", sections[2]),      # الباب الثاني
    ("03_Bab_3", sections[3]),      # الباب الثالث
    ("04_Bab_4", sections[4]),      # الباب الرابع
    ("05_Bab_5", sections[5]),      # الباب الخامس
    ("06_Bab_6", sections[6]),      # الباب السادس
]

for fname, content in file_map:
    path = os.path.join(output_dir, f"{fname}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content + "\n")
    print(f"  Created {path} ({len(content.splitlines())} lines)")

print(f"\nDone. {len(file_map)} files written to {output_dir}/")