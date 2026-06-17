from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.content_generator import ContentGenerator
from app.database.repository import SettingRepository

router = Router()


@router.callback_query(Text("settings"))
async def settings_menu(callback: types.CallbackQuery, session: AsyncSession):
    settings_repo = SettingRepository(session)
    settings = await settings_repo.get_or_create(callback.from_user.id)

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"{'✅' if settings.auto_posting_enabled else '❌'} Автопостинг",
        callback_data="toggle_autopost",
    )
    builder.button(text=f"⏰ Интервал: {settings.posting_interval_hours}ч", callback_data="set_interval")
    builder.button(text=f"🎨 Стиль: {settings.image_style or 'modern'}", callback_data="set_style")
    builder.button(text=f"🤖 Модель: {settings.openai_model or 'gpt-4o'}", callback_data="set_model")
    builder.button(text=f"🗣 Тон: {settings.content_tone or 'professional'}", callback_data="set_tone")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        f"• Автопостинг: {'Вкл' if settings.auto_posting_enabled else 'Выкл'}\n"
        f"• Интервал: {settings.posting_interval_hours} ч\n"
        f"• Стиль изображений: {settings.image_style or 'modern'}\n"
        f"• AI модель: {settings.openai_model or 'gpt-4o'}\n"
        f"• Тон контента: {settings.content_tone or 'professional'}\n"
        f"• Язык: {settings.language}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(Text("toggle_autopost"))
async def toggle_autopost(callback: types.CallbackQuery, session: AsyncSession):
    settings_repo = SettingRepository(session)
    settings = await settings_repo.get_or_create(callback.from_user.id)
    await settings_repo.update(
        callback.from_user.id, auto_posting_enabled=not settings.auto_posting_enabled
    )
    await settings_menu(callback, session)
    await callback.answer()


@router.callback_query(Text("set_style"))
async def set_style(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for style in ["modern minimalistic", "luxury aesthetic", "bold vibrant", "soft pastel", "dark moody"]:
        builder.button(text=style.capitalize(), callback_data=f"style_{style}")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.adjust(1)

    await callback.message.edit_text("🎨 Выбери стиль изображений:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("style_"))
async def apply_style(callback: types.CallbackQuery, session: AsyncSession):
    style = callback.data.replace("style_", "")
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, image_style=style)
    await settings_menu(callback, session)
    await callback.answer()


@router.callback_query(Text("set_model"))
async def set_model(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="GPT-4o", callback_data="model_gpt-4o")
    builder.button(text="GPT-4o-mini", callback_data="model_gpt-4o-mini")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.adjust(1)

    await callback.message.edit_text("🤖 Выбери AI модель:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("model_"))
async def apply_model(callback: types.CallbackQuery, session: AsyncSession):
    model = callback.data.replace("model_", "")
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, openai_model=model)
    await settings_menu(callback, session)
    await callback.answer()


@router.callback_query(Text("set_tone"))
async def set_tone(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for tone in ["professional", "inspirational", "luxury", "friendly", "trendy"]:
        builder.button(text=tone.capitalize(), callback_data=f"tone_{tone}")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.adjust(1)

    await callback.message.edit_text("🗣 Выбери тон контента:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("tone_"))
async def apply_tone(callback: types.CallbackQuery, session: AsyncSession):
    tone = callback.data.replace("tone_", "")
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, content_tone=tone)
    await settings_menu(callback, session)
    await callback.answer()


@router.callback_query(Text("set_interval"))
async def set_interval(callback: types.CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for hours in [3, 6, 12, 24]:
        builder.button(text=f"{hours} ч", callback_data=f"interval_{hours}")
    builder.button(text="🔙 Назад", callback_data="settings")
    builder.adjust(2)

    await callback.message.edit_text("⏰ Выбери интервал:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("interval_"))
async def apply_interval(callback: types.CallbackQuery, session: AsyncSession):
    hours = int(callback.data.replace("interval_", ""))
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, posting_interval_hours=hours)
    await settings_menu(callback, session)
    await callback.answer()
