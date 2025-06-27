
import os
from dotenv import load_dotenv

load_dotenv()

# Detect environment
IS_REPLIT = os.getenv("REPLIT_DB_URL") is not None
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None

# Determine mode
if IS_RAILWAY:
    MODE = "PRODUCTION"
    print(f"🚀 Environment: Railway (PRODUCTION)")
elif IS_REPLIT:
    MODE = "DEVELOPMENT"
    print(f"🔧 Environment: Replit (DEVELOPMENT)")
else:
    MODE = "LOCAL"
    print(f"💻 Environment: Local")

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

# Auto-detect web app URL based on environment
if IS_REPLIT:
    # For Replit development
    WEB_APP_URL = "https://workspace.CryptoGurman.repl.co"
elif IS_RAILWAY:
    # For Railway production
    WEB_APP_URL = "https://sasha-production.up.railway.app"
else:
    # Fallback
    WEB_APP_URL = os.getenv("WEB_APP_URL", "http://0.0.0.0:5000")

print(f"Web App URL: {WEB_APP_URL}")
print(f"Mode: {MODE}")

CHANNEL_LINK = "https://t.me/neizvestnyipabger"
TIKTOK_LINK = "https://www.tiktok.com/@neizvestiypubger"
TELEGRAM_LINK = "https://t.me/neizvestnyipabger"
