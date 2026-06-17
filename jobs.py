import json
from typing import Any

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.content_generator import ContentGenerator
from app.ai.image_generator import ImageGenerator
from app.database.repository import (
    ContentRepository,
    ImageRepository,
    PinRepository,
    SettingRepository,
)
from app.utils.config import config
from app.utils.logger import logger


class PinterestService:
    API_BASE = "https://api.pinterest.com/v5"

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pin_repo = PinRepository(session)
        self.content_repo = ContentRepository(session)
        self.image_repo = ImageRepository(session)
        self.settings_repo = SettingRepository(session)
        self.content_gen = ContentGenerator()
        self.image_gen = ImageGenerator()

    async def get_boards(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {config.pinterest_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.API_BASE}/boards", headers=headers) as resp:
                if resp.status != 200:
                    logger.error(f"Failed to fetch boards: {resp.status}")
                    return []
                data = await resp.json()
                return data.get("items", [])

    async def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        link: str | None = None,
    ) -> dict | None:
        headers = {"Authorization": f"Bearer {config.pinterest_token}"}
        payload = {
            "board_id": board_id,
            "title": title[:100],
            "description": description[:500],
            "media_source": {"source_type": "image_url", "url": image_url},
        }
        if link:
            payload["link"] = link
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.API_BASE}/pins", headers=headers, json=payload
            ) as resp:
                if resp.status not in (200, 201):
                    text = await resp.text()
                    logger.error(f"Failed to create pin: {resp.status} - {text}")
                    return None
                return await resp.json()

    async def create_and_publish_pin(self, user_id: int) -> dict | None:
        settings = await self.settings_repo.get_or_create(user_id)
        boards = settings.boards or []
        categories = settings.categories or self.content_gen.CATEGORIES

        if not boards:
            pinterest_boards = await self.get_boards()
            boards = [b["id"] for b in pinterest_boards]
            if not boards:
                logger.warning("No Pinterest boards available")
                return None

        content = await self.content_gen.generate_pin_content(
            category=categories[0] if isinstance(categories, list) else "beauty",
            tone=settings.content_tone or "professional",
        )

        content_data = json.loads(content) if isinstance(content, str) else content

        image_paths = await self.image_gen.generate_variations(
            prompt=content_data.get("image_prompt", "beauty aesthetic"),
            count=1,
            model=settings.image_generation_model or "openai",
        )

        if not image_paths:
            logger.error("Failed to generate images")
            return None

        image_url = f"file://{image_paths[0]}"

        pin = await self.pin_repo.create(
            user_id=user_id,
            title=content_data["pin_title"],
            description=content_data.get("description"),
            category=categories[0] if isinstance(categories, list) else "beauty",
            tags={"hashtags": content_data.get("hashtags", [])},
            seo_keywords={"keywords": content_data.get("seo_keywords", [])},
            cta_text=content_data.get("cta_text"),
            local_image_path=image_paths[0],
            is_ai_generated=True,
        )

        result = await self.create_pin(
            board_id=boards[0],
            title=content_data["pin_title"],
            description=content_data.get("description", ""),
            image_url=image_paths[0],
            link=config.telegram_channel_link or config.database_url,
        )

        if result:
            pin_id = result.get("id")
            await self.pin_repo.update(
                pin.id,
                pinterest_pin_id=pin_id,
                board_id=boards[0],
                is_published=True,
                published_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            )

        return result

    async def get_pin_analytics(self, pin_id: str) -> dict:
        headers = {"Authorization": f"Bearer {config.pinterest_token}"}
        url = f"{self.API_BASE}/pins/{pin_id}/analytics"
        params = {
            "metric_types": "IMPRESSION,SAVE,CLICK,OUTBOUND_CLICK",
            "start_date": "2024-01-01",
            "end_date": "2026-12-31",
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()

    async def get_user_analytics(self) -> dict:
        headers = {"Authorization": f"Bearer {config.pinterest_token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.API_BASE}/user_account/analytics", headers=headers
            ) as resp:
                if resp.status != 200:
                    return {}
                return await resp.json()
