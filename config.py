
import os
from dotenv import load_dotenv

load_dotenv()

# Detect environment
IS_REPLIT = os.getenv("REPLIT_DB_URL") is not None
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None

# PostgreSQL Configuration
DATABASE_PUBLIC_URL = os.getenv("DATABASE_PUBLIC_URL")
USE_POSTGRESQL = DATABASE_PUBLIC_URL is not None

# Determine mode
if IS_RAILWAY:
    MODE = "PRODUCTION"
    print(f"🚀 Environment: Railway (PRODUCTION) - Full Bot + Web")
elif IS_REPLIT:
    MODE = "DEVELOPMENT"
    print(f"🔧 Environment: Replit (DEVELOPMENT) - Full Bot + Web")
else:
    MODE = "LOCAL"
    print(f"💻 Environment: Local - Full Bot + Web")

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database configuration
USE_POSTGRESQL = DATABASE_PUBLIC_URL is not None

print(f"PostgreSQL URL configured: {bool(DATABASE_PUBLIC_URL)}")
print(f"Using PostgreSQL: {USE_POSTGRESQL}")

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
