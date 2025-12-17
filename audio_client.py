import os
import asyncio
import wave
from google import genai
from google.genai import types

INPUT_TEXT = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"

SYSTEM_INSTRUCTION = """
You are Quran Translation Voice, a text-to-audio assistant. Your job is to output ONLY the English translation of the provided Qur’anic Arabic, suitable to be spoken aloud.

Rules:
- Output ONLY the translation itself. Do NOT say “Surah”, “Ayah”, numbers, headings, or any meta text.
- Do NOT include Arabic, transliteration, commentary, tafsir, explanations, or notes.
- Be faithful to the Arabic meaning. Do not add details. Keep a dignified, neutral tone.
- Use clear modern English.
"""

async def main():
    config = types.LiveConnectConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_modalities=["AUDIO"],
        speech_config={"voice_config": {"prebuilt_voice_config": {"voice_name": "Charon"}}},
    )
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-preview-12-2025", config=config) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        await session.send_client_content(turns={"role": "user", "parts": [{"text": INPUT_TEXT}]}, turn_complete=True)
        async for response in session.receive():
            if response.server_content and response.server_content.model_turn:
                for part in response.server_content.model_turn.parts:
                    if part.text:
                        print(part.text)
                    elif hasattr(part, 'inline_data') and part.inline_data.data:
                        wf.writeframes(part.inline_data.data)
        wf.close()
        print("Finished writing to audio.wav")

if __name__ == "__main__":
    asyncio.run(main())