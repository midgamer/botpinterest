from datetime import datetime, timezone

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Analytic
from app.database.repository import AnalyticRepository, PinRepository
from app.utils.config import config
from app.utils.logger import logger


class AnalyticsCollector:
    PINTEREST_API_BASE = "https://api.pinterest.com/v5"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analytic_repo = AnalyticRepository(session)
        self.pin_repo = PinRepository(session)

    async def collect_pin_stats(self, pin_id: int) -> dict | None:
        pin = await self.pin_repo.get(pin_id)
        if not pin or not pin.pinterest_pin_id:
            return None
        headers = {"Authorization": f"Bearer {config.pinterest_token}"}
        url = f"{self.PINTEREST_API_BASE}/pins/{pin.pinterest_pin_id}/analytics"
        params = {
            "start_date": "2024-01-01",
            "end_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "metric_types": "IMPRESSION,SAVE,CLICK,OUTBOUND_CLICK",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        logger.error(f"Pinterest API error for pin {pin_id}: {resp.status}")
                        return None
                    data = await resp.json()
                    metrics = data.get("all", {})
                    analytic = await self.analytic_repo.create(
                        pin_id=pin_id,
                        impressions=metrics.get("IMPRESSION", {}).get("value", 0),
                        saves=metrics.get("SAVE", {}).get("value", 0),
                        clicks=metrics.get("CLICK", {}).get("value", 0),
                        outbound_clicks=metrics.get("OUTBOUND_CLICK", {}).get("value", 0),
                    )
                    return analytic
        except Exception as e:
            logger.error(f"Failed to collect analytics for pin {pin_id}: {e}")
            return None

    async def collect_all_pins_stats(self, user_id: int) -> int:
        pins = await self.pin_repo.list_by_user(user_id, is_published=True)
        count = 0
        for pin in pins:
            result = await self.collect_pin_stats(pin.id)
            if result:
                count += 1
        return count
