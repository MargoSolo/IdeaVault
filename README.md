# 🧠 IdeaVault — Voice & Text to Obsidian Bot

Telegram bot for seamless idea capture → GitHub → Obsidian.

**Stack:** Python · aiogram 3 · Google Gemini 2.5 Flash · PyGithub · Vercel


```
bot/
├── main.py              # Vercel entry point + local polling
├── bot.py               # Telegram handlers (aiogram)
├── gemini_processor.py  # Voice transcription + classification (Gemini)
├── github_uploader.py   # Creates .md files via GitHub API
├── requirements.txt
├── vercel.json
├── .env                 # ← secrets (do not commit!)
 
```

---

## Quick Start (local)
```bash
cd obs/bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run in polling mode (no webhook needed)
python main.py
```

Open Telegram → find your bot → send text or a voice message.

---

## Deploy to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Log in
```bash
vercel login
```
 
### 3. Deploy with environment variables
```bash
cd obs/bot
vercel --prod \
  -e TG_TOKEN="your_telegram_bot_token_here" \
  -e GOOGLE_API_KEY="your_google_ai_studio_api_key_here" \
  -e GITHUB_TOKEN="your_github_personal_access_token_here" \
  -e GITHUB_REPO="YourUsername/your-obsidian-repo" \
  -e ALLOWED_USER_ID="your_telegram_user_id_here"
```
 

After deployment, Vercel will show a URL like `https://your-bot-xyz.vercel.app`.

### 4. Set the Telegram webhook
```bash
curl "https://api.telegram.org/bot<YOUR_TG_TOKEN>/setWebhook?url=https://your-bot-xyz.vercel.app/webhook"
```

✅ Done! You can now send voice messages and text to the bot. 
---

## Obsidian Git Setup

1. Install the **Obsidian Git** plugin from Community Plugins.
2. Open plugin settings:
   - `Remote URL` → `https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git`
   - `Authentication method` → Personal Access Token
   - Paste the same `GITHUB_TOKEN`
3. Enable **Auto pull** every 5–10 minutes.

Notes will automatically appear in Obsidian after each message to the bot.

---

## Folder Logic

| Folder | When it's used |
|--------|----------------|
| `00_Inbox` | Thoughts, observations — anything unstructured |
| `10_Projects` | Action items, plans, features |
| `20_Education` | Courses, lectures, university, books |
| `30_Articles` | Post ideas, blog drafts, writing |---

## Security

- The bot responds **only** to messages from a single authorized `ALLOWED_USER_ID`
- All secrets are stored in `.env` / Vercel environment variables
- `.gitignore` excludes `.env` from the repository
