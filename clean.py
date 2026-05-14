import re

input_file = "Fazail-e-Sadaqat_OCR.md"
output_file = "Fazail-e-Sadaqat_Clean.txt"

with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

# Remove '## Page X' markers
text = re.sub(r'^## Page \d+\s*$', '', text, flags=re.MULTILINE)

# Remove horizontal rules '---'
text = re.sub(r'^---\s*$', '', text, flags=re.MULTILINE)

# Remove SKIP markers
text = re.sub(r'^\s*<!-- SKIPPED:.*?-->\s*$', '', text, flags=re.MULTILINE)

# Remove extra empty lines (optional, but good for cleanliness)
text = re.sub(r'\n{3,}', '\n\n', text)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(text.strip())

print(f"Cleaned text saved to {output_file}")