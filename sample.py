import os
import asyncio
from gemini_webapi import GeminiClient
from gemini_webapi.constants import Model


async def main():
    client = GeminiClient(
        secure_1psid=os.environ.get("SECURE_1PSID"),
        secure_1psidts=os.environ.get("SECURE_1PSIDTS"),
    )
    await client.init()

    model = Model.BASIC_FLASH
    response = await client.generate_content(
        "Tell me a joke about AI.",
        model=model,
    )

    print(f"Model: {model.model_name}")
    print(f"Response: {response.text}")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())