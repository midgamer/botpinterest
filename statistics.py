from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.optimizer import StrategyOptimizer
from app.bot.services.pinterest import PinterestService

router = Router()


@router.callback_query(Text("pinterest_analytics"))
async def pinterest_analytics_menu(callback: types.CallbackQuery, session: AsyncSession):
    pinterest = PinterestService(session)
    user_analytics = await pinterest.get_user_analytics()
    boards = await pinterest.get_boards()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить аналитику", callback_data="refresh_analytics")
    builder.button(text="💡 Рекомендации AI", callback_data="ai_recommendations")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    msg = "📈 <b>Pinterest Аналитика</b>\n\n"
    if user_analytics:
        metrics = user_analytics.get("all", {})
        msg += (
            f"👁 Показы: {metrics.get('IMPRESSION', {}).get('value', 'N/A')}\n"
            f"💾 Сохранения: {metrics.get('SAVE', {}).get('value', 'N/A')}\n"
            f"🖱 Клики: {metrics.get('CLICK', {}).get('value', 'N/A')}\n"
        )
    else:
        msg += "Нет данных аналитики.\n"
    msg += f"\n📋 Досок: {len(boards)}"

    await callback.message.edit_text(msg, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(Text("refresh_analytics"))
async def refresh_analytics(callback: types.CallbackQuery, session: AsyncSession):
    from app.analytics.collector import AnalyticsCollector

    collector = AnalyticsCollector(session)
    count = await collector.collect_all_pins_stats(callback.from_user.id)
    await callback.message.edit_text(f"✅ Собрана аналитика для {count} пинов.")
    await callback.answer()


@router.callback_query(Text("ai_recommendations"))
async def ai_recommendations(callback: types.CallbackQuery, session: AsyncSession):
    await callback.message.edit_text("💡 AI анализирует статистику и готовит рекомендации...")
    optimizer = StrategyOptimizer(session)
    recs = await optimizer.generate_recommendations(callback.from_user.id)
    await callback.message.edit_text(
        f"💡 <b>Рекомендации AI</b>\n\n{recs}",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Назад", callback_data="pinterest_analytics"
        ).as_markup(),
    )
    await callback.answer()
