from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    Analytic,
    GeneratedContent,
    GeneratedImage,
    Pin,
    Reference,
    SchedulerJob,
    Setting,
    User,
)


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, **kwargs) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id, **kwargs)
            self.session.add(user)
            await self.session.flush()
        return user

    async def get(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def update(self, user_id: int, **kwargs) -> User | None:
        await self.session.execute(update(User).where(User.id == user_id).values(**kwargs))
        return await self.get(user_id)


class PinRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, **kwargs) -> Pin:
        pin = Pin(user_id=user_id, **kwargs)
        self.session.add(pin)
        await self.session.flush()
        return pin

    async def get(self, pin_id: int) -> Pin | None:
        result = await self.session.execute(select(Pin).where(Pin.id == pin_id))
        return result.scalar_one_or_none()

    async def get_by_uuid(self, uuid: str) -> Pin | None:
        result = await self.session.execute(select(Pin).where(Pin.uuid == uuid))
        return result.scalar_one_or_none()

    async def update(self, pin_id: int, **kwargs) -> Pin | None:
        await self.session.execute(update(Pin).where(Pin.id == pin_id).values(**kwargs))
        return await self.get(pin_id)

    async def list_by_user(
        self, user_id: int, limit: int = 20, offset: int = 0, is_published: bool | None = None
    ) -> list[Pin]:
        query = select(Pin).where(Pin.user_id == user_id)
        if is_published is not None:
            query = query.where(Pin.is_published == is_published)
        query = query.order_by(desc(Pin.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_stats(self, user_id: int) -> dict:
        total = await self.session.scalar(
            select(func.count(Pin.id)).where(Pin.user_id == user_id)
        )
        published = await self.session.scalar(
            select(func.count(Pin.id)).where(and_(Pin.user_id == user_id, Pin.is_published == True))
        )
        ai_generated = await self.session.scalar(
            select(func.count(Pin.id)).where(and_(Pin.user_id == user_id, Pin.is_ai_generated == True))
        )
        return {"total": total or 0, "published": published or 0, "ai_generated": ai_generated or 0}

    async def get_recent_published(self, user_id: int, days: int = 30) -> list[Pin]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(Pin)
            .where(and_(Pin.user_id == user_id, Pin.is_published == True, Pin.published_at >= cutoff))
            .order_by(desc(Pin.published_at))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class AnalyticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, pin_id: int, **kwargs) -> Analytic:
        analytic = Analytic(pin_id=pin_id, **kwargs)
        self.session.add(analytic)
        await self.session.flush()
        return analytic

    async def get_by_pin(self, pin_id: int, limit: int = 30) -> list[Analytic]:
        query = (
            select(Analytic)
            .where(Analytic.pin_id == pin_id)
            .order_by(desc(Analytic.collected_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_aggregated(self, user_id: int, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(
                func.sum(Analytic.impressions).label("total_impressions"),
                func.sum(Analytic.saves).label("total_saves"),
                func.sum(Analytic.clicks).label("total_clicks"),
                func.sum(Analytic.outbound_clicks).label("total_outbound_clicks"),
                func.avg(Analytic.ctr).label("avg_ctr"),
                func.count(func.distinct(Analytic.pin_id)).label("unique_pins"),
            )
            .select_from(Analytic)
            .join(Pin, Analytic.pin_id == Pin.id)
            .where(and_(Pin.user_id == user_id, Analytic.collected_at >= cutoff))
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "impressions": row.total_impressions or 0,
            "saves": row.total_saves or 0,
            "clicks": row.total_clicks or 0,
            "outbound_clicks": row.total_outbound_clicks or 0,
            "avg_ctr": round(float(row.avg_ctr or 0), 2),
            "unique_pins": row.unique_pins or 0,
        }

    async def get_daily_series(self, user_id: int, days: int = 30) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(
                func.date(Analytic.collected_at).label("date"),
                func.sum(Analytic.impressions).label("impressions"),
                func.sum(Analytic.saves).label("saves"),
                func.sum(Analytic.clicks).label("clicks"),
            )
            .select_from(Analytic)
            .join(Pin, Analytic.pin_id == Pin.id)
            .where(and_(Pin.user_id == user_id, Analytic.collected_at >= cutoff))
            .group_by(func.date(Analytic.collected_at))
            .order_by("date")
        )
        result = await self.session.execute(query)
        return [dict(row._mapping) for row in result.all()]


class ReferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Reference:
        ref = Reference(**kwargs)
        self.session.add(ref)
        await self.session.flush()
        return ref

    async def get(self, ref_id: int) -> Reference | None:
        result = await self.session.execute(select(Reference).where(Reference.id == ref_id))
        return result.scalar_one_or_none()

    async def list(
        self, category: str | None = None, limit: int = 20, offset: int = 0
    ) -> list[Reference]:
        query = select(Reference)
        if category:
            query = query.where(Reference.category == category)
        query = query.order_by(desc(Reference.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete(self, ref_id: int) -> None:
        await self.session.execute(delete(Reference).where(Reference.id == ref_id))


class ContentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> GeneratedContent:
        content = GeneratedContent(**kwargs)
        self.session.add(content)
        await self.session.flush()
        return content

    async def get_unused(self, category: str | None = None) -> GeneratedContent | None:
        query = select(GeneratedContent).where(GeneratedContent.is_used == False)
        if category:
            query = query.where(GeneratedContent.category == category)
        query = query.order_by(desc(GeneratedContent.created_at)).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_used(self, content_id: int) -> None:
        await self.session.execute(
            update(GeneratedContent).where(GeneratedContent.id == content_id).values(is_used=True)
        )


class ImageRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, content_id: int, **kwargs) -> GeneratedImage:
        image = GeneratedImage(content_id=content_id, **kwargs)
        self.session.add(image)
        await self.session.flush()
        return image

    async def select_image(self, image_id: int) -> None:
        await self.session.execute(
            update(GeneratedImage).where(GeneratedImage.id == image_id).values(is_selected=True)
        )


class SettingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> Setting:
        result = await self.session.execute(select(Setting).where(Setting.user_id == user_id))
        setting = result.scalar_one_or_none()
        if not setting:
            setting = Setting(user_id=user_id)
            self.session.add(setting)
            await self.session.flush()
        return setting

    async def update(self, user_id: int, **kwargs) -> Setting | None:
        await self.session.execute(update(Setting).where(Setting.user_id == user_id).values(**kwargs))
        return await self.get_or_create(user_id)


class SchedulerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> SchedulerJob:
        job = SchedulerJob(**kwargs)
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_active(self) -> list[SchedulerJob]:
        result = await self.session.execute(
            select(SchedulerJob).where(SchedulerJob.is_active == True)
        )
        return list(result.scalars().all())

    async def update(self, job_id: str, **kwargs) -> None:
        await self.session.execute(
            update(SchedulerJob).where(SchedulerJob.job_id == job_id).values(**kwargs)
        )
