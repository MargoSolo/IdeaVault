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

SYSTEM_PROMPT = """You are an intelligent assistant for organising notes in Obsidian.
Analyse the text and return ONLY valid JSON (no markdown fences, raw JSON only) in the following format:

{
  "folder": "<one of: 00_Inbox | 10_Projects | 20_Education | 30_Articles | 40_Travel>",
  "title": "<short note title in English, 5-7 words>",
  "tags": ["<tag1>", "<tag2>"],
  "body": "<full note body in Markdown format>"
}

Folder selection rules:
- 00_Inbox: random thoughts, ideas, quick notes on the go.
- 10_Projects: tasks, feature descriptions, plans, projects.
- 20_Education: studying, courses, books, ITMO, Vigo, lectures, university.
- 30_Articles: ideas for posts, articles, blogs, notes for publication.
- 40_Travel: travel, tickets, restaurants, hotels, visas, countries, trip plans.

Tag rules:
- Maximum 3-5 tags. Lowercase only, no #.

Body rules:
- Make the text CLEAN and WELL-STRUCTURED. Use headings (#, ##), lists, and bold where appropriate.
- Remove filler words and repetitions from voice messages. Make the text coherent, as if written by a professional editor.
- Do not add greetings, intros, or closing remarks. Only the structured idea.
"""


def _clean_json(raw: str) -> dict:
    """Strip markdown code fences if Gemini wrapped the JSON."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


async def process_text(text: str) -> dict:
    """Classify a plain text message and return structured note data."""
    prompt = f"{SYSTEM_PROMPT}\n\nUser text:\n{text}"
    response = _client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return _clean_json(response.text)


async def process_voice(ogg_bytes: bytes) -> dict:
    """Transcribe a voice OGG file and classify it."""
    transcribe_prompt = (
        "First, transcribe the voice message ACCURATELY — "
        "remove filler words but preserve the meaning. "
        "Then classify according to the instructions below.\n\n"
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
