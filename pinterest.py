from pathlib import Path

from aiogram import Router, types
from aiogram.filters import Text
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.callback_query(Text("logs"))
async def logs_menu(callback: types.CallbackQuery):
    log_dir = Path("logs")
    log_files = sorted(log_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True) if log_dir.exists() else []

    builder = InlineKeyboardBuilder()
    for lf in log_files[:10]:
        name = lf.name
        size = lf.stat().st_size
        label = f"{name} ({size // 1024}KB)" if size > 1024 else name
        builder.button(text=label, callback_data=f"view_log_{name}")
    builder.button(text="🗑 Очистить логи", callback_data="clear_logs")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(1)

    msg = "📋 <b>Логи системы</b>\n\n"
    if log_files:
        msg += f"Найдено {len(log_files)} лог-файлов.\nВыбери файл для просмотра:"
    else:
        msg += "Лог-файлы не найдены."

    await callback.message.edit_text(msg, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("view_log_"))
async def view_log(callback: types.CallbackQuery):
    filename = callback.data.replace("view_log_", "")
    log_path = Path("logs") / filename
    if not log_path.exists():
        await callback.message.answer(f"❌ Файл {filename} не найден.")
        await callback.answer()
        return

    content = log_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    last_lines = lines[-50:]
    text = "\n".join(last_lines)

    msg = f"📋 <b>{filename}</b> (последние 50 строк):\n\n<code>{text}</code>"
    await callback.message.answer(msg[:4000])
    await callback.answer()


@router.callback_query(Text("clear_logs"))
async def clear_logs(callback: types.CallbackQuery):
    log_dir = Path("logs")
    if log_dir.exists():
        for f in log_dir.glob("*.log"):
            f.write_text("")
    await callback.message.edit_text("✅ Логи очищены.")
    await callback.answer()
