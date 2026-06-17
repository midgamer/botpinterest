import json

from aiogram import Router, types
from aiogram.filters import Text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.content_generator import ContentGenerator
from app.ai.image_generator import ImageGenerator
from app.database.repository import ContentRepository, ImageRepository

router = Router()
content_gen = ContentGenerator()
image_gen = ImageGenerator()


@router.callback_query(Text("create_content"))
async def create_content_menu(callback: types.CallbackQuery):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for cat in content_gen.CATEGORIES:
        builder.button(text=cat.capitalize(), callback_data=f"gen_content_{cat}")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(2)

    await callback.message.edit_text(
        "📝 <b>Создание контента</b>\n\nВыбери категорию:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("gen_content_"))
async def generate_content(callback: types.CallbackQuery, session: AsyncSession):
    category = callback.data.replace("gen_content_", "")
    await callback.message.edit_text(f"🎨 Генерирую контент для категории <b>{category}</b>...")

    content = await content_gen.generate_pin_content(category=category)
    content_data = json.loads(content) if isinstance(content, str) else content

    content_repo = ContentRepository(session)
    db_content = await content_repo.create(
        pin_title=content_data["pin_title"],
        description=content_data.get("description"),
        seo_keywords={"keywords": content_data.get("seo_keywords", [])},
        hashtags={"hashtags": content_data.get("hashtags", [])},
        cta_text=content_data.get("cta_text"),
        category=category,
    )

    await callback.message.answer(
        f"✅ <b>Контент сгенерирован!</b>\n\n"
        f"<b>Заголовок:</b> {content_data['pin_title']}\n\n"
        f"<b>Описание:</b> {content_data.get('description', '')[:300]}...\n\n"
        f"<b>Хэштеги:</b> {' '.join(content_data.get('hashtags', []))}\n\n"
        f"<b>CTA:</b> {content_data.get('cta_text', '')}\n\n"
        f"🎨 Генерирую изображение..."
    )

    image_prompt = content_data.get("image_prompt", f"{category} beauty aesthetic")
    image_paths = await image_gen.generate_variations(prompt=image_prompt, count=3)

    image_repo = ImageRepository(session)
    for path in image_paths:
        await image_repo.create(content_id=db_content.id, file_path=path, prompt=image_prompt)

    if image_paths:
        from aiogram.types import FSInputFile
        photo = FSInputFile(image_paths[0])
        await callback.message.answer_photo(
            photo=photo,
            caption=f"📌 <b>{content_data['pin_title']}</b>\n\n{content_data.get('cta_text', '')}",
            reply_markup=await get_content_actions_keyboard(db_content.id),
        )

    await callback.answer()


async def get_content_actions_keyboard(content_id: int):
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Получить готовый контент", callback_data=f"show_content_{content_id}")
    builder.button(text="🔄 Создать похожее", callback_data=f"similar_{content_id}")
    builder.button(text="💾 Сохранить в референсы", callback_data=f"save_ref_{content_id}")
    builder.button(text="🔙 В меню", callback_data="back_to_menu")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(lambda c: c.data and c.data.startswith("show_content_"))
async def show_content(callback: types.CallbackQuery, session: AsyncSession):
    content_id = int(callback.data.replace("show_content_", ""))
    from app.database.models import GeneratedContent
    from sqlalchemy import select

    result = await session.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        await callback.message.answer("❌ Контент не найден.")
        await callback.answer()
        return

    seo = content.seo_keywords or {}
    tags = content.hashtags or {}
    seo_list = ", ".join(seo.get("keywords", []))
    tags_list = " ".join(tags.get("hashtags", []))

    msg = (
        f"📌 <b>{content.pin_title}</b>\n\n"
        f"<b>Описание:</b>\n{content.description}\n\n"
        f"<b>SEO ключевые слова:</b>\n{seo_list}\n\n"
        f"<b>Хэштеги:</b>\n{tags_list}\n\n"
        f"<b>CTA для Telegram:</b>\n{content.cta_text or '—'}\n\n"
        f"<i>✅ Контент готов. Когда захочешь включить автопостинг в Pinterest — "
        f"зайди в меню «Настройки» → «Автопостинг».</i>"
    )
    await callback.message.answer(msg[:4000])
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("similar_"))
async def create_similar(callback: types.CallbackQuery, session: AsyncSession):
    content_id = int(callback.data.replace("similar_", ""))
    from app.database.models import GeneratedContent
    from sqlalchemy import select

    result = await session.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
    original = result.scalar_one_or_none()
    if original:
        await generate_content(callback, session)
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("save_ref_"))
async def save_reference(callback: types.CallbackQuery, session: AsyncSession):
    content_id = int(callback.data.replace("save_ref_", ""))
    from app.database.models import GeneratedContent
    from sqlalchemy import select

    result = await session.execute(select(GeneratedContent).where(GeneratedContent.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        await callback.message.answer("❌ Контент не найден.")
        await callback.answer()
        return

    from app.database.repository import ReferenceRepository
    ref_repo = ReferenceRepository(session)
    await ref_repo.create(
        source="ai_generated",
        title=content.pin_title,
        original_text=content.description,
        category=content.category,
        tags=content.hashtags,
        ai_summary=f"AI-сгенерированный контент. CTA: {content.cta_text}",
    )
    await callback.message.answer("💾 <b>Сохранено в библиотеку референсов!</b>")
    await callback.answer()
