from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SchedulerJob
from app.database.repository import SchedulerRepository
from app.utils.logger import logger


class SchedulerManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._jobs: dict[str, str] = {}

    def start(self):
        self.scheduler.start()
        logger.info("Scheduler started")

    def stop(self):
        self.scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    def add_job(
        self,
        job_id: str,
        func,
        interval_minutes: int,
        name: str = "",
        **kwargs,
    ):
        trigger = IntervalTrigger(minutes=interval_minutes, timezone=timezone.utc)
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=True,
            **kwargs,
        )
        self._jobs[job_id] = name or job_id
        logger.info(f"Job '{job_id}' scheduled every {interval_minutes} min")

    def remove_job(self, job_id: str):
        try:
            self.scheduler.remove_job(job_id)
            self._jobs.pop(job_id, None)
            logger.info(f"Job '{job_id}' removed")
        except Exception as e:
            logger.error(f"Failed to remove job '{job_id}': {e}")

    def get_jobs(self) -> list[dict]:
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "interval": str(job.trigger),
                }
            )
        return jobs

    async def restore_jobs(self, session: AsyncSession):
        repo = SchedulerRepository(session)
        active_jobs = await repo.get_active()
        for job in active_jobs:
            logger.info(f"Found active job in DB: {job.job_id} ({job.name})")
