import os
import sys
import json
from mistralai.client import Mistral

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

filename = sys.argv[1]

uploaded_pdf = client.files.upload(
    file={"file_name": filename, "content": open(filename, "rb")},
    purpose="ocr"
)
signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)

ocr_response = client.ocr.process(
    model="mistral-ocr-latest",
    document={"type": "document_url", "document_url": signed_url.url},
    include_image_base64=True
)

client.files.delete(file_id=uploaded_pdf.id)

output_file = os.path.splitext(filename)[0] + "-ocr-response.json"
with open(output_file, "w") as f:
    f.write(ocr_response.model_dump_json(indent=2))

print(f"Saved to {output_file}")
