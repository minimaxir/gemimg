import os

import httpx
from dotenv import load_dotenv

load_dotenv()


class gemimg:
    def __init__(self, model="gemini-2.5-flash"):
        assert os.getenv("GEMINI_API_KEY"), "Gemini API key is not defined in .env."
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = httpx.Client()
        self.model = model

    def generate(self, system, temperature=1.0):
        query_params = {
            "generationConfig": {
                "temperature": temperature,
            },
            "system_instruction": {"parts": [{"text": system.strip()}]},
            "contents": [{"parts": [{"text": ""}]}],
        }

        params = {"key": self.api_key}

        headers = {
            "Content-Type": "application/json",
        }

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

        try:
            r = self.client.post(
                api_url, params=params, json=query_params, headers=headers, timeout=600
            )
        except httpx.exceptions.Timeout:
            return None

        try:
            gen_text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except KeyError:
            print(r.json())

        return gen_text, r.json()
