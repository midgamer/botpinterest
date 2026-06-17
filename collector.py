import json
from pathlib import Path
from typing import Any

import aiohttp
from openai import AsyncOpenAI

from app.utils.config import config
from app.utils.helpers import slugify


class ImageGenerator:
    IMAGE_DIR = Path("app/images/generated")
    IMAGE_SIZE = "1024x1792"

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        self.IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    async def generate_with_openai(self, prompt: str, style: str = "vivid") -> str:
        response = await self.openai_client.images.generate(
            model="dall-e-3",
            prompt=f"{prompt}. Style: {style}, beautiful feminine aesthetic, high quality, 4k, Pinterest style",
            size=self.IMAGE_SIZE,
            quality="hd",
            n=1,
        )
        image_url = response.data[0].url
        return await self._download_image(image_url, slugify(prompt[:50]))

    async def generate_with_flux(self, prompt: str) -> str:
        if not config.flux_api_key:
            return await self.generate_with_openai(prompt)
        async with aiohttp.ClientSession() as session:
            payload = {
                "prompt": f"{prompt}, 1000x1500, high quality, Pinterest aesthetic, beauty",
                "width": 1000,
                "height": 1500,
                "steps": 30,
            }
            headers = {"Authorization": f"Bearer {config.flux_api_key}"}
            async with session.post(
                "https://api.bfl.ml/v1/image", json=payload, headers=headers
            ) as resp:
                data = await resp.json()
                image_url = data.get("url") or data.get("image_url", "")
                return await self._download_image(image_url, slugify(prompt[:50]))

    async def generate_variations(
        self, prompt: str, count: int = 3, model: str = "openai"
    ) -> list[str]:
        paths = []
        for i in range(count):
            if model == "flux":
                path = await self.generate_with_flux(f"{prompt} variation {i+1}")
            else:
                path = await self.generate_with_openai(f"{prompt} variation {i+1}")
            paths.append(path)
        return paths

    async def _download_image(self, url: str, name: str) -> str:
        import uuid

        filename = f"{name}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = self.IMAGE_DIR / filename
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                content = await resp.read()
                filepath.write_bytes(content)
        return str(filepath)
