from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import SettingRepository

router = Router()


@router.callback_query(Text("autoposting"))
async def autoposting_menu(callback: types.CallbackQuery, session: AsyncSession):
    settings_repo = SettingRepository(session)
    settings = await settings_repo.get_or_create(callback.from_user.id)

    mode = "Pinterest" if settings.auto_posting_enabled else "Telegram"
    interval = settings.posting_interval_hours

    builder = InlineKeyboardBuilder()
    if settings.auto_posting_enabled:
        builder.button(text="⏹ Остановить", callback_data="autopost_stop")
        builder.button(text="📋 Доски Pinterest", callback_data="autopost_boards")
    else:
        builder.button(text="📄 Показать готовый контент", callback_data="autopost_demo")
        builder.button(text="▶️ Включить Pinterest", callback_data="autopost_enable_prompt")
    builder.button(text="⏰ Интервал", callback_data="autopost_interval")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        f"🤖 <b>Автопостинг</b>\n\n"
        f"Режим: <b>{mode}</b>\n"
        f"Интервал: {interval} ч\n\n"
        f"🔸 <b>Сейчас</b> — контент приходит тебе в Telegram.\n"
        f"🔸 <b>Хочешь в Pinterest?</b> — нажми «Включить Pinterest», "
        f"и ничего не сломается — код уже готов.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(Text("autopost_demo"))
async def autopost_demo(callback: types.CallbackQuery):
    await callback.message.answer(
        "📄 <b>Как получить контент:</b>\n\n"
        "1. Нажми «📝 Создать контент» в главном меню\n"
        "2. Выбери категорию\n"
        "3. После генерации нажми «📄 Получить готовый контент»\n\n"
        "Всё придёт сюда, в Telegram."
    )
    await callback.answer()


@router.callback_query(Text("autopost_enable_prompt"))
async def autopost_enable_prompt(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да, включить", callback_data="autopost_start")
    builder.button(text="🔙 Пока нет", callback_data="autoposting")
    builder.adjust(1)

    await callback.message.edit_text(
        "📌 <b>Включить автопостинг в Pinterest?</b>\n\n"
        "После включения бот начнёт публиковать пины "
        "на твою Pinterest-доску по расписанию.\n\n"
        "Убедись, что в <code>.env</code> указан <code>PINTEREST_TOKEN</code>.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(Text("autopost_start"))
async def autopost_start(callback: types.CallbackQuery, session: AsyncSession):
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, auto_posting_enabled=True)
    await callback.message.edit_text(
        "✅ <b>Автопостинг в Pinterest включён!</b>\n\n"
        "Теперь бот будет публиковать пины. "
        "Вернись в меню, чтобы настроить интервал."
    )
    await callback.answer()


@router.callback_query(Text("autopost_stop"))
async def autopost_stop(callback: types.CallbackQuery, session: AsyncSession):
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, auto_posting_enabled=False)
    await callback.message.edit_text(
        "⏹ <b>Автопостинг остановлен.</b>\n"
        "Контент снова будет приходить в Telegram."
    )
    await callback.answer()


@router.callback_query(Text("autopost_interval"))
async def autopost_interval(callback: types.CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for hours in [3, 6, 12, 24]:
        builder.button(text=f"{hours} ч", callback_data=f"set_interval_{hours}")
    builder.button(text="🔙 Назад", callback_data="autoposting")
    builder.adjust(2)

    await callback.message.edit_text("⏰ Выбери интервал автопостинга:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("set_interval_"))
async def set_interval(callback: types.CallbackQuery, session: AsyncSession):
    hours = int(callback.data.replace("set_interval_", ""))
    settings_repo = SettingRepository(session)
    await settings_repo.update(callback.from_user.id, posting_interval_hours=hours)
    await callback.message.edit_text(f"✅ Интервал установлен: {hours} ч")
    await callback.answer()
