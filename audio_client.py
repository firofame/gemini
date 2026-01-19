import os
import asyncio
import wave
from google import genai
from google.genai import types

INPUT_TEXT = "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ"

SYSTEM_INSTRUCTION = "Provide a clear, natural, and respectful phonetic transcription of the input text."

async def main():
    config = types.LiveConnectConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        response_modalities=["AUDIO"],
        speech_config={
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Charon"
                }
            }
        },
    )
    
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    async with client.aio.live.connect(
        model="gemini-2.5-flash-native-audio-latest",
        config=config
    ) as session:
        wf = wave.open("audio.wav", "wb")
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)

        await session.send_client_content(
            turns={"role": "user", "parts": [{"text": INPUT_TEXT}]},
            turn_complete=True
        )
        
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