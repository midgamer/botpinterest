import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.bot.handlers import (
    analytics, autoposting, content, logs,
    menu, references, settings, start, statistics, trends,
)
from app.database.session import async_session_factory, init_db, close_db
from app.scheduler.jobs import ScheduledJobs
from app.scheduler.manager import SchedulerManager
from app.utils.config import config
from app.utils.logger import logger, setup_logger

setup_logger()

bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = SchedulerManager()
scheduled_jobs = ScheduledJobs(async_session_factory)

dp.include_routers(
    start.router, menu.router, content.router, autoposting.router,
    statistics.router, trends.router, analytics.router, references.router,
    settings.router, logs.router,
)


class DBSessionMiddleware:
    async def __call__(self, handler, event, data):
        async with async_session_factory() as session:
            try:
                data["session"] = session
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise


dp.update.middleware(DBSessionMiddleware())


async def on_startup():
    await init_db()
    scheduler.add_job(
        "collect_analytics", scheduled_jobs.collect_analytics,
        interval_minutes=1440, name="Collect Analytics",
    )
    scheduler.add_job(
        "discover_trends", scheduled_jobs.discover_trends,
        interval_minutes=1440, name="Discover Trends",
    )
    scheduler.start()
    await bot.set_webhook(f"{config.bot_webhook_url}/webhook")
    logger.info("Bot started via webhook")


async def on_shutdown():
    scheduler.stop()
    await close_db()
    await bot.session.close()
    logger.info("Bot stopped")


async def health(request):
    return web.json_response({"status": "ok"}, status=200)


def main():
    app = web.Application()

    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path="/webhook")

    app.on_startup.append(lambda _: asyncio.create_task(on_startup()))
    app.on_shutdown.append(lambda _: asyncio.create_task(on_shutdown()))
    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=3000)


if __name__ == "__main__":
    main()
