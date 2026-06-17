import json
from typing import Any

from openai import AsyncOpenAI

from app.utils.config import config


class TrendAnalyzer:
    REGIONS = ["USA", "Europe", "Japan", "Korea", "China"]

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def analyze_trends(self, category: str, region: str = "USA") -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — аналитик мировых трендов в Beauty-индустрии. "
                        "Отвечай JSON с актуальными трендами."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Проанализируй текущие тренды в категории '{category}' для региона {region}. "
                        "Верни JSON:\n"
                        '- "trends": массив объектов с полями "name", "description", "keywords", "engagement_level"\n'
                        '- "region": регион\n'
                        '- "category": категория\n'
                        '- "summary": краткое резюме трендов на русском\n'
                        'Учти текущую дату: 2026 год.'
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        return json.loads(response.choices[0].message.content)

    async def get_global_trends(self, category: str) -> list[dict[str, Any]]:
        results = []
        for region in self.REGIONS:
            trends = await self.analyze_trends(category, region)
            results.append({"region": region, "trends": trends})
        return results

    async def find_content_opportunities(self, category: str) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — стратег контент-маркетинга в Beauty-нише. "
                        "Находи незанятые ниши и возможности для вирального контента."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Найди 5 контентных возможностей в категории '{category}' для Pinterest. "
                        "Верни JSON:\n"
                        '- "opportunities": массив объектов с полями "topic", "angle", "target_audience", "why_viral"\n'
                        '- "best_posting_time": лучшее время для публикации\n'
                        '- "recommended_hashtags": массив рекомендованных хэштегов'
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )
        return json.loads(response.choices[0].message.content)
