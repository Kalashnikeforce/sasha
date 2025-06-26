
import asyncio
import logging
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, IS_REPLIT, IS_RAILWAY
from handlers import register_handlers
from database import init_db
from web_app import create_app
from aiohttp import web

# Configure logging based on environment
if IS_RAILWAY:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(level=logging.INFO)

# Global variables for cleanup
app_runner = None
bot_instance = None
dp_instance = None

async def cleanup():
    """Cleanup function for graceful shutdown"""
    global app_runner, bot_instance, dp_instance
    
    if dp_instance:
        await dp_instance.stop_polling()
    
    if bot_instance:
        await bot_instance.session.close()
    
    if app_runner:
        await app_runner.cleanup()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down gracefully...")
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup())

async def main():
    global app_runner, bot_instance, dp_instance
    
    # Initialize database
    await init_db()
    
    # Initialize bot and dispatcher
    bot_instance = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp_instance = Dispatcher(storage=storage)
    
    # Register handlers
    register_handlers(dp_instance, bot_instance)
    
    # Determine port based on environment
    if IS_RAILWAY:
        port = int(os.getenv("PORT", 8080))
    else:
        port = 5000
    
    # Create web app
    app = await create_app(bot_instance)
    
    # Start web server
    app_runner = web.AppRunner(app)
    await app_runner.setup()
    site = web.TCPSite(app_runner, '0.0.0.0', port)
    await site.start()
    
    environment = "Railway (Production)" if IS_RAILWAY else "Replit (Development)" if IS_REPLIT else "Local"
    print(f"Bot and web app started on port {port}! Environment: {environment}")
    print(f"Web app available at: http://0.0.0.0:{port}")
    
    if IS_RAILWAY:
        print(f"Railway deployment URL: https://sasha-production.up.railway.app")
        print(f"Listening on 0.0.0.0:{port}")
        print("Railway environment variables:", {
            "PORT": os.getenv("PORT"),
            "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT")
        })
    
    # Set up signal handlers for graceful shutdown
    if IS_RAILWAY:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Start polling (this will run indefinitely)
    try:
        await dp_instance.start_polling(bot_instance)
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Error during polling: {e}")
    finally:
        await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
