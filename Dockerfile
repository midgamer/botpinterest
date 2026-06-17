from app.analytics.collector import AnalyticsCollector
from app.bot.services.pinterest import PinterestService
from app.database.repository import SettingRepository
from app.utils.config import config
from app.utils.logger import logger


class ScheduledJobs:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.owner_id = config.owner_id

    async def auto_post_to_pinterest(self):
        logger.info("Running scheduled auto-post to Pinterest")
        async with self.session_factory() as session:
            settings_repo = SettingRepository(session)
            pinterest = PinterestService(session)
            settings = await settings_repo.get_or_create(self.owner_id)
            if not settings.auto_posting_enabled:
                logger.info("Auto-posting disabled, skipping")
                return
            result = await pinterest.create_and_publish_pin(self.owner_id)
            if result:
                logger.info("Auto-posted pin successfully")
            else:
                logger.warning("Auto-post: no content available to publish")

    async def collect_analytics(self):
        logger.info("Running scheduled analytics collection")
        async with self.session_factory() as session:
            collector = AnalyticsCollector(session)
            count = await collector.collect_all_pins_stats(self.owner_id)
            logger.info(f"Collected analytics for {count} pins")

    async def discover_trends(self):
        logger.info("Running scheduled trend discovery")
        from app.ai.trend_analyzer import TrendAnalyzer

        analyzer = TrendAnalyzer()
        for category in ["skincare", "makeup", "self-care", "beauty hacks"]:
            try:
                trends = await analyzer.analyze_trends(category, "USA")
                trend_count = len(trends.get("trends", []))
                logger.info(f"Trends for {category}: {trend_count} trends found")
            except Exception as e:
                logger.error(f"Failed to discover trends for {category}: {e}")
