import asyncio
import sys
from pathlib import Path

import redis.asyncio as aioredis
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bot.handlers import (
    analytics,
    autoposting,
    content,
    logs,
    menu,
    references,
    settings,
    start,
    statistics,
    trends,
)
from app.database.session import async_session_factory, close_db, init_db
from app.scheduler.jobs import ScheduledJobs
from app.scheduler.manager import SchedulerManager
from app.utils.config import config
from app.utils.logger import logger, setup_logger


class BeautyBot:
    def __init__(self):
        setup_logger()
        self.bot = Bot(
            token=config.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        self.redis = None
        self.storage = None
        self.dp = Dispatcher()
        self.scheduler = SchedulerManager()
        self.scheduled_jobs = ScheduledJobs(async_session_factory)

    async def setup_redis(self):
        try:
            self.redis = await aioredis.from_url(
                config.redis_url, decode_responses=True
            )
            self.storage = RedisStorage(redis=self.redis)
            self.dp = Dispatcher(storage=self.storage)
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis unavailable, using memory storage: {e}")
            self.dp = Dispatcher()

    async def setup_handlers(self):
        self.dp.include_routers(
            start.router,
            menu.router,
            content.router,
            autoposting.router,
            statistics.router,
            trends.router,
            analytics.router,
            references.router,
            settings.router,
            logs.router,
        )
        logger.info("Handlers registered")

    async def setup_middleware(self):
        from aiogram import BaseMiddleware
        from typing import Any, Awaitable, Callable

        class DBSessionMiddleware(BaseMiddleware):
            async def __call__(
                self,
                handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
                event: types.TelegramObject,
                data: dict[str, Any],
            ) -> Any:
                async with async_session_factory() as session:
                    try:
                        data["session"] = session
                        return await handler(event, data)
                    except Exception:
                        await session.rollback()
                        raise

        self.dp.update.middleware(DBSessionMiddleware())
        logger.info("Middleware registered")

    async def setup_scheduler(self):
        jobs = self.scheduled_jobs

        # Автопостинг в Pinterest отключён.
        # Весь контент приходит в Telegram.
        # Раскомментируй ниже, чтобы включить автопостинг.
        # self.scheduler.add_job(
        #     "auto_post", jobs.auto_post_to_pinterest, interval_minutes=360, name="Auto-post to Pinterest"
        # )
        self.scheduler.add_job(
            "collect_analytics", jobs.collect_analytics, interval_minutes=1440, name="Collect Pinterest Analytics"
        )
        self.scheduler.add_job(
            "discover_trends", jobs.discover_trends, interval_minutes=1440, name="Discover Global Trends"
        )
        self.scheduler.start()
        logger.info("Scheduler jobs configured (auto-post to Pinterest disabled)")

    async def setup_webhook(self):
        await self.bot.delete_webhook(drop_pending_updates=True)

    async def start(self):
        logger.info("Starting Beauty Pinterest Bot...")

        if not config.bot_token or config.bot_token == "your_telegram_bot_token_here":
            logger.error("BOT_TOKEN not configured! Set it in .env file.")
            return

        await init_db()
        logger.info("Database initialized")

        await self.setup_redis()
        await self.setup_handlers()
        await self.setup_middleware()
        await self.setup_scheduler()
        await self.setup_webhook()

        logger.info(f"Bot started. Owner ID: {config.owner_id}")
        try:
            await self.dp.start_polling(self.bot, skip_updates=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        logger.info("Shutting down...")
        self.scheduler.stop()
        await close_db()
        if self.redis:
            await self.redis.close()
        await self.bot.session.close()
        logger.info("Shutdown complete")


async def main():
    bot = BeautyBot()
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
