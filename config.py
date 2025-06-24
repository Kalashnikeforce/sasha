import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = "bot_database.db"
CHANNEL_ID = "@neizvestnyipabger"
# Get admin IDs from environment variable or use empty list
admin_ids_str = os.getenv("ADMIN_IDS", "")
if admin_ids_str:
    try:
        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    except ValueError:
        print("Warning: Invalid ADMIN_IDS format. Using empty list.")
        ADMIN_IDS = []
else:
    ADMIN_IDS = []

print(f"Configured admin IDs: {ADMIN_IDS}")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-repl-url.replit.dev")
CHANNEL_LINK = "https://t.me/neizvestnyipabger"
TIKTOK_LINK = "https://www.tiktok.com/@neizvestiypubger"
TELEGRAM_LINK = "https://t.me/neizvestnyipabger"