from typing import Any

from openai import AsyncOpenAI

from app.utils.config import config


class ContentGenerator:
    CATEGORIES = [
        "skincare", "makeup", "self-care", "luxury beauty",
        "perfumes", "feminine energy", "beauty hacks", "haircare",
    ]

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def generate_pin_content(
        self,
        category: str,
        keywords: list[str] | None = None,
        tone: str = "professional",
        reference_text: str | None = None,
    ) -> dict[str, Any]:
        prompt = self._build_generation_prompt(category, keywords, tone, reference_text)
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — профессиональный AI-копирайтер для Pinterest в Beauty-нише. "
                        "Твоя задача — создавать виральные пины, которые привлекают клики в Telegram-канал. "
                        "Отвечай строго в JSON формате."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        return response.choices[0].message.content

    def _build_generation_prompt(
        self,
        category: str,
        keywords: list[str] | None,
        tone: str,
        reference: str | None,
    ) -> str:
        kw = ", ".join(keywords) if keywords else "beauty, skincare, trends"
        ref_section = f"\n\nОриентируйся на этот референсный текст: {reference}" if reference else ""
        return f"""
Сгенерируй контент для Pinterest-пина в категории "{category}".
Тон: {tone}.
Ключевые слова: {kw}.
{ref_section}

Верни JSON со следующими полями:
- "pin_title": заголовок пина (до 100 символов, цепляющий внимание)
- "description": описание пина (до 500 символов, с призывом подписаться на Telegram-канал)
- "seo_keywords": массив SEO-ключевых слов (5-10 штук)
- "hashtags": массив хэштегов (5-10 штук, на русском и английском)
- "cta_text": текст призыва к действию для Telegram (до 60 символов)
- "image_prompt": промпт для генерации изображения (на английском, до 300 символов)
"""

    async def generate_batch(
        self, category: str, count: int = 5, tone: str = "professional"
    ) -> list[dict[str, Any]]:
        results = []
        for _ in range(count):
            content = await self.generate_pin_content(category=category, tone=tone)
            results.append(content)
        return results
