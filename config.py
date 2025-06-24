
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_PATH = "bot_database.db"
CHANNEL_ID = "@neizvestnyipabger"
CHANNEL_LINK = "https://t.me/neizvestnyipabger"
TIKTOK_LINK = "https://www.tiktok.com/@neizvestiypubger"
TELEGRAM_LINK = "https://t.me/neizvestnyipabger"
WEB_APP_URL = os.getenv("WEB_APP_URL")

# Admin user IDs from environment
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip().isdigit()]
