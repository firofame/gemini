from google import genai
from pydantic import BaseModel
from typing import List
import json
import os
from pathlib import Path

class Word(BaseModel):
    text: str
    start: float
    end: float

class Segment(BaseModel):
    start: float
    end: float
    words: List[Word]

class Transcript(BaseModel):
    segments: List[Segment]

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
myfile = client.files.upload(file="audio.mp3")
prompt = "Transcribe and translate audio. Output word-level timestamps for karaoke display. Output only English translation."

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[prompt, myfile],
    config={
        "response_mime_type": "application/json",
        "response_schema": Transcript.model_json_schema(),
    },
)

data = json.loads(response.text)
Path("audio.json").write_text(json.dumps(data["segments"], ensure_ascii=False, indent=2))