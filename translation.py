from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.start import get_main_keyboard

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: types.Message):
    await message.answer("📌 Главное меню:", reply_markup=await get_main_keyboard())


@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📌 Главное меню:", reply_markup=await get_main_keyboard()
    )
    await callback.answer()
