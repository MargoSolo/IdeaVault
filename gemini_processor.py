"""
gemini_processor.py
Handles voice transcription and text classification via Google Gemini 1.5 Flash.
Uses the new google-genai SDK (google.genai).
"""
import json
import re
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """Ты — интеллектуальный помощник для организации заметок в Obsidian.
Проанализируй текст и верни ТОЛЬКО валидный JSON (без markdown-блоков, только сырой JSON) в следующем формате:

{
  "folder": "<одно из: 00_Inbox | 10_Projects | 20_Education | 30_Articles | 40_Travel>",
  "title": "<короткое название заметки на русском, 5-7 слов>",
  "tags": ["<тег1>", "<тег2>"],
  "body": "<полное тело заметки в формате Markdown>"
}

Правила выбора папки:
- 00_Inbox: мысли, идеи, заметки «на бегу».
- 10_Projects: задачи, описание фич, планы, проекты.
- 20_Education: учёба, курсы, книги, ИТМО, Vigo, лекции, университет.
- 30_Articles: идеи для постов, статьи, блога, заметки для публикации.
- 40_Travel: 여행, билеты, рестораны, отели, визы, страны, планы поездок.

Правила для тегов:
- Максимум 3-5 тегов. Только строчные буквы, без #.

Правила для body:
- Сделай текст ЧИСТЫМ и КРАСИВЫМ. Используй заголовки (#, ##), списки и жирный шрифт где уместно.
- Убери все «э», «ну», «вот» и повторы из голосовых. Сделай текст связным, как будто ты профессиональный редактор.
- Не добавляй приветствий, вступлений или заключений от себя. Только структурированная мысль.
"""


def _clean_json(raw: str) -> dict:
    """Strip markdown code fences if Gemini wrapped the JSON."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


async def process_text(text: str) -> dict:
    """Classify a plain text message and return structured note data."""
    prompt = f"{SYSTEM_PROMPT}\n\nТекст пользователя:\n{text}"
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return _clean_json(response.text)


async def process_voice(ogg_bytes: bytes) -> dict:
    """Transcribe a voice OGG file and classify it."""
    transcribe_prompt = (
        "Сначала ТОЧНО расшифруй голосовое сообщение — "
        "убери слова-паразиты, но сохрани смысл. "
        "Затем классифицируй по инструкции ниже.\n\n"
        + SYSTEM_PROMPT
    )

    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=ogg_bytes, mime_type="audio/ogg"),
            transcribe_prompt,
        ],
    )
    return _clean_json(response.text)
