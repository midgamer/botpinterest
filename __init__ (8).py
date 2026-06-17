from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.ai.trend_analyzer import TrendAnalyzer

router = Router()
trend_analyzer = TrendAnalyzer()


@router.callback_query(Text("world_trends"))
async def world_trends_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for region in trend_analyzer.REGIONS:
        builder.button(text=region, callback_data=f"trends_region_{region}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(2)

    await callback.message.edit_text(
        "🌍 <b>Мировые тренды</b>\n\nВыбери регион для анализа:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("trends_region_"))
async def show_region_trends(callback: types.CallbackQuery):
    region = callback.data.replace("trends_region_", "")
    await callback.message.edit_text(f"🔍 Анализирую тренды для региона <b>{region}</b>...")

    try:
        trends = await trend_analyzer.analyze_trends(category="beauty", region=region)
        msg = f"🌍 <b>Тренды: {region}</b>\n\n"
        for t in trends.get("trends", []):
            name = t.get("name", "N/A")
            desc = t.get("description", "")
            engagement = t.get("engagement_level", "medium")
            msg += f"• <b>{name}</b>\n  {desc[:100]}\n  Уровень: {engagement}\n\n"
        msg += f"\n📝 <b>Резюме:</b> {trends.get('summary', '')[:200]}"
        await callback.message.edit_text(msg, reply_markup=await get_trends_back_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


@router.callback_query(Text("beauty_trends"))
async def beauty_trends_menu(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    categories = [
        ("skincare", "beauty_trend_skincare"),
        ("makeup", "beauty_trend_makeup"),
        ("self-care", "beauty_trend_selfcare"),
        ("luxury beauty", "beauty_trend_luxury"),
        ("perfumes", "beauty_trend_perfumes"),
    ]
    for text, cb in categories:
        builder.button(text=text.capitalize(), callback_data=cb)
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(2)

    await callback.message.edit_text(
        "💄 <b>Beauty тренды</b>\n\nВыбери категорию:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("beauty_trend_"))
async def show_beauty_trend(callback: types.CallbackQuery):
    category_map = {
        "skincare": "skincare", "makeup": "makeup", "selfcare": "self-care",
        "luxury": "luxury beauty", "perfumes": "perfumes",
    }
    key = callback.data.replace("beauty_trend_", "")
    category = category_map.get(key, key)
    await callback.message.edit_text(f"🔍 Анализирую тренды в категории <b>{category}</b>...")

    try:
        trends = await trend_analyzer.analyze_trends(category=category, region="Worldwide")
        opportunities = await trend_analyzer.find_content_opportunities(category=category)

        msg = f"💄 <b>Beauty тренды: {category}</b>\n\n"
        for t in trends.get("trends", []):
            msg += f"• <b>{t.get('name', '')}</b>\n  {t.get('description', '')[:150]}\n\n"

        if opportunities.get("best_posting_time"):
            msg += f"⏰ <b>Лучшее время публикации:</b> {opportunities['best_posting_time']}\n\n"

        if opportunities.get("recommended_hashtags"):
            msg += f"🏷 <b>Рекомендуемые хэштеги:</b>\n{' '.join(opportunities['recommended_hashtags'][:10])}"

        await callback.message.edit_text(msg, reply_markup=await get_trends_back_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {e}")
    await callback.answer()


async def get_trends_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    return builder.as_markup()
