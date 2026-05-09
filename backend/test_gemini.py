import asyncio
from google import genai

async def test():
    try:
        client = genai.Client(vertexai=True, location="europe-west1")
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents='Say hello.'
        )
        print("Response:", response.text)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
