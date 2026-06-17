from app.ai.summarizer import Summarizer
from app.utils.config import config


class TranslationService:
    def __init__(self):
        self.summarizer = Summarizer()
        self.use_deepl = bool(config.deepl_api_key)

    async def translate(self, text: str, target_lang: str = "ru") -> str:
        return await self.summarizer.translate_text(text, target_lang)

    async def summarize(self, text: str, max_length: int = 200) -> str:
        return await self.summarizer.summarize_text(text, max_length)
