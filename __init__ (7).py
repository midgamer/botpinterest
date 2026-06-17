from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import ReferenceRepository

router = Router()


@router.callback_query(Text("references"))
async def references_menu(callback: types.CallbackQuery, session: AsyncSession):
    ref_repo = ReferenceRepository(session)
    refs = await ref_repo.list(limit=10)

    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Сохранить референс", callback_data="add_reference")
    builder.button(text="📚 Все референсы", callback_data="all_references")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    msg = "🖼 <b>Библиотека референсов</b>\n\n"
    if refs:
        for ref in refs[:5]:
            msg += f"• <b>{ref.title or 'Без названия'}</b> [{ref.source}]\n"
            if ref.ai_summary:
                msg += f"  {ref.ai_summary[:100]}...\n"
            msg += "\n"
    else:
        msg += "Референсов пока нет.\nСначала сохраните контент или найдите тренды."

    await callback.message.edit_text(msg, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(Text("all_references"))
async def all_references(callback: types.CallbackQuery, session: AsyncSession):
    ref_repo = ReferenceRepository(session)
    refs = await ref_repo.list(limit=50)

    if not refs:
        await callback.message.edit_text("📭 Референсов нет.")
        await callback.answer()
        return

    msg = "📚 <b>Все референсы</b>\n\n"
    for i, ref in enumerate(refs, 1):
        msg += f"{i}. <b>{ref.title or 'N/A'}</b> | {ref.source} | {ref.category or 'Без категории'}\n"

    await callback.message.edit_text(
        msg[:3500],
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Назад", callback_data="references"
        ).as_markup(),
    )
    await callback.answer()
