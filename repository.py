from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import UserRepository, SettingRepository
from app.utils.config import config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    user_repo = UserRepository(session)
    user = await user_repo.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        language_code=message.from_user.language_code,
        is_owner=(message.from_user.id == config.owner_id),
    )

    settings_repo = SettingRepository(session)
    await settings_repo.get_or_create(user.id)

    if not user.is_active:
        await message.answer("Доступ запрещен.")
        return

    await message.answer(
        "✨ <b>Beauty Pinterest Bot</b> ✨\n\n"
        "Я помогаю продвигать Telegram-канал через Pinterest в Beauty-нише.\n"
        "Я анализирую мировые тренды, создаю контент, генерирую изображения "
        "и автоматически публикую пины.\n\n"
        "Используй меню ниже чтобы начать:",
        reply_markup=await get_main_keyboard(),
    )


async def get_main_keyboard():
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    buttons = [
        ("📝 Создать контент", "create_content"),
        ("🤖 Автопостинг", "autoposting"),
        ("📊 Статистика", "statistics"),
        ("🌍 Тренды мира", "world_trends"),
        ("💄 Beauty тренды", "beauty_trends"),
        ("📈 Pinterest аналитика", "pinterest_analytics"),
        ("🖼 Референсы", "references"),
        ("⚙️ Настройки", "settings"),
        ("📋 Логи", "logs"),
    ]
    for text, callback in buttons:
        builder.button(text=text, callback_data=callback)
    builder.adjust(2)
    return builder.as_markup()
