from datetime import datetime, timezone
from typing import Any

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import AnalyticRepository, PinRepository
from app.utils.config import config


class StrategyOptimizer:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytic_repo = AnalyticRepository(session)
        self.pin_repo = PinRepository(session)
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def analyze_performance(self, user_id: int, days: int = 30) -> dict[str, Any]:
        stats = await self.analytic_repo.get_aggregated(user_id, days)
        pins = await self.pin_repo.get_recent_published(user_id, days)

        best_pin = max(pins, key=lambda p: self._get_pin_engagement(p)) if pins else None
        worst_pin = min(pins, key=lambda p: self._get_pin_engagement(p)) if pins else None

        return {
            "stats": stats,
            "best_pin": best_pin,
            "worst_pin": worst_pin,
            "total_pins_analyzed": len(pins),
        }

    async def generate_recommendations(self, user_id: int) -> str:
        performance = await self.analyze_performance(user_id)
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты — AI-маркетолог. На основе аналитики Pinterest дай рекомендации "
                        "по улучшению стратегии продвижения. Ответ на русском."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Вот статистика за 30 дней:\n"
                        f"Impressions: {performance['stats']['impressions']}\n"
                        f"Saves: {performance['stats']['saves']}\n"
                        f"Clicks: {performance['stats']['clicks']}\n"
                        f"CTR: {performance['stats']['avg_ctr']}%\n\n"
                        f"Проанализируй и дай 3-5 конкретных рекомендаций "
                        f"для улучшения вовлеченности и кликов в Telegram."
                    ),
                },
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()

    def _get_pin_engagement(self, pin) -> int:
        if not pin.analytics:
            return 0
        return sum(a.saves + a.clicks for a in pin.analytics)
