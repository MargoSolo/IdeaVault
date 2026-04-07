"""
main.py
Vercel serverless entry point.

- In production (Vercel): receives Telegram webhook POST → feeds to aiogram
- In local dev: falls back to long-polling so you can test without deploying
"""
import asyncio
import json
import logging
import os
import sys

from aiogram.types import Update
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Create a global event loop for the Vercel Python runtime
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# -------------------------------------------------------------------
# Vercel serverless handler
# -------------------------------------------------------------------
async def _process_update(body: bytes) -> None:
    """Parse a raw Telegram update and feed it to the dispatcher."""
    from bot import bot, dp

    update = Update.model_validate(json.loads(body))
    await dp.feed_update(bot, update)

from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """
    Vercel Python runtime HTTP request handler.
    """
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len)
        try:
            loop.run_until_complete(_process_update(post_body))
        except Exception as e:
            logger.error("Error processing update: %s", e)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"OK")


# -------------------------------------------------------------------
# Local development: long-polling (no webhook needed)
# -------------------------------------------------------------------
async def _run_polling() -> None:
    from bot import bot, dp

    logger.info("Starting in long-polling mode (local dev)…")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(_run_polling())
