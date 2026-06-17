from aiogram import Router, types
from aiogram.filters import Text
from aiogram.types import FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.charts import ChartBuilder
from app.database.repository import AnalyticRepository, PinRepository

router = Router()
chart_builder = ChartBuilder()


@router.callback_query(Text("statistics"))
async def statistics_menu(callback: types.CallbackQuery, session: AsyncSession):
    pin_repo = PinRepository(session)
    analytic_repo = AnalyticRepository(session)
    stats = await pin_repo.get_stats(callback.from_user.id)
    analytics = await analytic_repo.get_aggregated(callback.from_user.id, 30)

    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"📌 <b>Пины:</b>\n"
        f"Всего: {stats['total']}\n"
        f"Опубликовано: {stats['published']}\n"
        f"AI-сгенерировано: {stats['ai_generated']}\n\n"
        f"📈 <b>Аналитика (30 дней):</b>\n"
        f"👁 Показы: {analytics['impressions']}\n"
        f"💾 Сохранения: {analytics['saves']}\n"
        f"🖱 Клики: {analytics['clicks']}\n"
        f"↗️ CTR: {analytics['avg_ctr']}%",
        reply_markup=await get_statistics_keyboard(),
    )
    await callback.answer()


async def get_statistics_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.button(text="📈 Показать графики", callback_data="show_charts")
    builder.button(text="📋 Список пинов", callback_data="pin_list")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(Text("show_charts"))
async def show_charts(callback: types.CallbackQuery, session: AsyncSession):
    analytic_repo = AnalyticRepository(session)
    data = await analytic_repo.get_daily_series(callback.from_user.id, 30)

    if not data:
        await callback.message.answer("📭 Нет данных для построения графиков.")
        await callback.answer()
        return

    chart_path = chart_builder.create_metrics_chart(data)

    if chart_path:
        photo = FSInputFile(chart_path)
        await callback.message.answer_photo(photo=photo, caption="📈 Аналитика за 30 дней")

    await callback.answer()
