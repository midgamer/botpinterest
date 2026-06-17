import json
from typing import Any

from openai import AsyncOpenAI

from app.utils.config import config


class Summarizer:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def summarize_text(self, text: str, max_length: int = 200) -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — AI-ассистент. Сделай краткое резюме текста на русском языке."},
                {"role": "user", "content": f"Суммируй этот текст (максимум {max_length} символов):\n\n{text}"},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()

    async def translate_text(self, text: str, target_lang: str = "ru") -> str:
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты — профессиональный переводчик. Переведи текст точно и естественно."},
                {"role": "user", "content": f"Переведи на {target_lang}:\n\n{text}"},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()

    async def analyze_image_content(self, image_url: str) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Проанализируй это изображение для Beauty-ниши. Верни JSON:\n"
                                '- "category": категория\n'
                                '- "colors": массив основных цветов\n'
                                '- "style": стиль изображения\n'
                                '- "mood": настроение\n'
                                '- "tags": массив тегов\n'
                                '- "description": краткое описание на русском'
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=500,
        )
        return json.loads(response.choices[0].message.content)
