"""
bot.py
Telegram bot handlers using aiogram 3.x.
Implements the "acknowledge first, then process" pattern to stay within
Vercel's 10-second function timeout.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from dotenv import load_dotenv

from gemini_processor import process_text, process_voice
from github_uploader import upload_note

load_dotenv()

logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(os.environ["ALLOWED_USER_ID"])

bot = Bot(token=os.environ["TG_TOKEN"])
dp = Dispatcher()


def _is_allowed(message: Message) -> bool:
    return message.from_user and message.from_user.id == ALLOWED_USER_ID


async def _handle_and_upload(message: Message, data: dict) -> None:
    """Process Gemini result and upload to GitHub, then notify user."""
    try:
        url = upload_note(data)
        tags_str = " ".join(f"#{t}" for t in data.get("tags", []))
        
        response = (
            f"✨ **{data['title']}**\n\n"
            f"📁 **Рубрика:** `{data['folder']}`\n"
            f"🏷 **Теги:** {tags_str}\n\n"
            f"--- 💠 ---\n\n"
            f"🔗 [Посмотреть в GitHub]({url})"
        )
        await message.answer(response, parse_mode="Markdown")
    except Exception as e:
        logger.error("Failed to upload note: %s", e)
        await message.answer(f"❌ **Ошибка сохранения:** {e}")


@dp.message(F.text.in_({"/start", "/help", "помощь"}))
async def cmd_help(message: Message) -> None:
    if not _is_allowed(message):
        return
        
    welcome_text = (
        "💎 **Личный Ассистент Заметок**\n\n"
        "Я помогу тебе мгновенно захватывать идеи и раскладывать их по полочкам в Obsidian.\n\n"
        "📌 **Доступные рубрики:**\n"
        "📥 `00_Inbox` — Мысли и идеи «на бегу»\n"
        "🏗 `10_Projects` — Задачи, фичи и планы\n"
        "🎓 `20_Education` — Учёба, книги и лекции\n"
        "✍️ `30_Articles` — Идеи для постов и блогов\n"
        "✈️ `40_Travel` — Билеты, отели и планы поездок\n\n"
        "🚀 **Как пользоваться:**\n"
        "1. Просто отправь **текст** или **голос**.\n"
        "2. Я сам выберу рубрику и подберу теги.\n"
        "3. Заметка сразу улетит на GitHub.\n\n"
        "🎨 *Всё будет оформлено чисто и профессионально!*"
    )
    await message.answer(welcome_text, parse_mode="Markdown")


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    if not _is_allowed(message):
        logger.warning("Blocked message from user_id=%s", message.from_user.id if message.from_user else "unknown")
        return

    # Acknowledge immediately so Telegram doesn't retry and Vercel doesn't timeout
    ack = await message.answer("⏳ Обрабатываю...")

    try:
        data = await process_text(message.text)
        await ack.delete()
        await _handle_and_upload(message, data)
    except Exception as e:
        logger.error("Text processing error: %s", e)
        await ack.delete()
        await message.answer(f"❌ Ошибка обработки: {e}")


@dp.message(F.voice)
async def handle_voice(message: Message) -> None:
    if not _is_allowed(message):
        return

    # Acknowledge immediately
    ack = await message.answer("🎙 Слушаю и расшифровываю...")

    try:
        # Download the voice file as bytes
        file_info = await bot.get_file(message.voice.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        ogg_bytes = downloaded.read()

        data = await process_voice(ogg_bytes)
        await ack.delete()
        await _handle_and_upload(message, data)
    except Exception as e:
        logger.error("Voice processing error: %s", e)
        await ack.delete()
        await message.answer(f"❌ Ошибка обработки голоса: {e}")


@dp.message(F.document)
async def handle_document(message: Message) -> None:
    """Accept .md files dropped directly into the chat."""
    if not _is_allowed(message):
        return

    doc = message.document
    if not doc.file_name.endswith(".md"):
        await message.answer("⚠️ Поддерживаются только .md файлы.")
        return

    ack = await message.answer("📄 Читаю файл...")
    try:
        file_info = await bot.get_file(doc.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        text = downloaded.read().decode("utf-8")

        data = await process_text(text)
        await ack.delete()
        await _handle_and_upload(message, data)
    except Exception as e:
        logger.error("Document processing error: %s", e)
        await ack.delete()
        await message.answer(f"❌ Ошибка обработки файла: {e}")
