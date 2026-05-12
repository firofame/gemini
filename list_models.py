import os
import asyncio
from gemini_webapi import GeminiClient


async def main():
    client = GeminiClient(
        secure_1psid=os.environ.get("SECURE_1PSID"),
        secure_1psidts=os.environ.get("SECURE_1PSIDTS"),
    )
    await client.init()
    models = client.list_models()
    if models:
        for m in models:
            print(f"{m.model_name:40s} {m.description}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
