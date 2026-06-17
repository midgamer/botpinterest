import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    pinterest_token: str = field(default_factory=lambda: os.getenv("PINTEREST_TOKEN", ""))
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/beauty_bot",
        )
    )
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    deepl_api_key: str = field(default_factory=lambda: os.getenv("DEEPL_API_KEY", ""))
    owner_id: int = field(default_factory=lambda: int(os.getenv("OWNER_ID", "0")))
    flux_api_key: str = field(default_factory=lambda: os.getenv("FLUX_API_KEY", ""))
    telegram_channel_link: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHANNEL_LINK", ""))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    bot_webhook_url: str = field(default_factory=lambda: os.getenv("BOT_WEBHOOK_URL", ""))

    @property
    def is_owner(self, user_id: int) -> bool:
        return user_id == self.owner_id


config = Config()
